import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { QuestionModel } from "@/modules/case/domain/model/case-model";

import { CaseRunner } from "./CaseRunner";

const questions: QuestionModel[] = [
  {
    id: 1,
    text: "Most likely diagnosis?",
    kind: "single_choice",
    position: 0,
    options: [
      { id: 11, text: "MI", score: 2, position: 0 },
      { id: 12, text: "Angina", score: 0, position: 1 },
    ],
  },
  {
    id: 2,
    text: "ECG finding?",
    kind: "single_choice",
    position: 1,
    options: [
      { id: 13, text: "STEMI", score: 1, position: 0 },
      { id: 14, text: "Normal", score: 0, position: 1 },
    ],
  },
];

function submissionResponse(): Response {
  return new Response(
    JSON.stringify({
      id: 1,
      case_id: 1,
      earned: "3",
      maximum: "3",
      percentage: "100.00",
      per_question: [
        { question_id: 1, selected_option_id: 11, score: "2", max_score: "2" },
        { question_id: 2, selected_option_id: 13, score: "1", max_score: "1" },
      ],
    }),
    { status: 201 },
  );
}

function radio(name: RegExp): HTMLElement {
  return screen.getByRole("radio", { name });
}

function submit(): void {
  fireEvent.submit(screen.getByRole("button", { name: /submit diagnosis/i }));
}

function answerAllCorrectly(): void {
  fireEvent.click(radio(/^MI/));
  fireEvent.click(radio(/^STEMI/));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("CaseRunner", () => {
  it("submits the selected answers and shows the scored breakdown", async () => {
    const fetchMock = vi.fn(async () => submissionResponse());
    vi.stubGlobal("fetch", fetchMock);

    render(<CaseRunner caseId={1} questions={questions} />);
    answerAllCorrectly();
    submit();

    await waitFor(() => expect(screen.getByText("100%")).toBeInTheDocument());
    expect(screen.getByText("3 of 3 points")).toBeInTheDocument();
    expect(screen.getByText("2 / 2 points")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("names the unanswered questions and does not submit", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    render(<CaseRunner caseId={1} questions={questions} />);
    fireEvent.click(radio(/^MI/));
    submit();

    expect(screen.getByRole("alert")).toHaveTextContent(/question 2/i);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("jumps to an unanswered question from the attempt panel", () => {
    render(<CaseRunner caseId={1} questions={questions} />);

    fireEvent.click(screen.getByRole("button", { name: /go to question 2/i }));

    expect(document.getElementById("question-2")).toHaveFocus();
  });

  it("locks the questions and marks the answers after submitting", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => submissionResponse()),
    );

    render(<CaseRunner caseId={1} questions={questions} />);
    answerAllCorrectly();
    submit();

    await waitFor(() => expect(screen.getByText("100%")).toBeInTheDocument());
    expect(radio(/^MI/)).toBeDisabled();
    expect(screen.getAllByText("Correct")).toHaveLength(2);
  });

  it("shows an error and keeps selections when the submission fails", async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response(JSON.stringify({ type: "server_error", title: "Boom" }), { status: 500 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<CaseRunner caseId={1} questions={questions} />);
    answerAllCorrectly();
    submit();

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Boom"));
    expect(radio(/^MI/)).toBeChecked();
  });

  it("resets the attempt and unlocks the questions when the user retakes the case", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => submissionResponse()),
    );

    render(<CaseRunner caseId={1} questions={questions} />);
    answerAllCorrectly();
    submit();
    await waitFor(() => expect(screen.getByText("100%")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /take again/i }));

    expect(screen.queryByText("100%")).not.toBeInTheDocument();
    expect(radio(/^MI/)).not.toBeChecked();
    expect(radio(/^MI/)).not.toBeDisabled();
  });
});
