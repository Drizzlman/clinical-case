import { afterEach, describe, expect, it, vi } from "vitest";

import { Failure, Success } from "@/modules/common/domain/operation-result";

import { CaseRepository } from "./case-repository";

afterEach(() => {
  vi.unstubAllGlobals();
});

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("CaseRepository.getCase", () => {
  it("maps the DTO to a domain Model on success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        jsonResponse({
          id: 1,
          title: "MI",
          description: null,
          questions: [
            {
              id: 1,
              text: "Most likely diagnosis?",
              kind: "single_choice",
              position: 0,
              options: [{ id: 11, text: "MI", score: "2", position: 0 }],
            },
          ],
        }),
      ),
    );

    const result = await CaseRepository.getCase(1);

    expect(result).toBeInstanceOf(Success);
    if (result instanceof Success) {
      expect(result.value.title).toBe("MI");
      expect(result.value.questions[0].options[0].score).toBe(2);
    }
  });

  it("returns a Failure carrying the status on a 404 problem", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        jsonResponse({ type: "not_found", title: "Resource not found" }, 404),
      ),
    );

    const result = await CaseRepository.getCase(999);

    expect(result).toBeInstanceOf(Failure);
    if (result instanceof Failure) {
      expect(result.status).toBe(404);
      expect(result.message).toBe("Resource not found");
    }
  });

  it("returns a Failure instead of throwing on a network error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new Error("boom"))),
    );

    const result = await CaseRepository.getCase(1);

    expect(result).toBeInstanceOf(Failure);
    if (result instanceof Failure) {
      expect(result.message).toBe("boom");
    }
  });
});

describe("CaseRepository.listCases", () => {
  it("maps the collection", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        jsonResponse([{ id: 1, title: "MI", description: null, question_count: 3 }]),
      ),
    );

    const result = await CaseRepository.listCases();

    expect(result).toBeInstanceOf(Success);
    if (result instanceof Success) {
      expect(result.value).toEqual([
        { id: 1, title: "MI", description: null, questionCount: 3 },
      ]);
    }
  });
});

describe("CaseRepository.submitAnswers", () => {
  it("posts JSON and maps the result", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          id: 1,
          case_id: 1,
          earned: "3",
          maximum: "3",
          percentage: "100.00",
          per_question: [
            { question_id: 1, selected_option_id: 11, score: "2", max_score: "2" },
          ],
        }),
        { status: 201 },
      ),
    );

    const result = await CaseRepository.submitAnswers({
      caseId: 1,
      answers: [{ questionId: 1, optionId: 11 }],
    });

    const init = fetchMock.mock.calls[0]?.[1] as RequestInit | undefined;
    expect(init?.method).toBe("POST");
    expect(init?.headers).toEqual({ "content-type": "application/json" });
    expect(JSON.parse(init?.body as string)).toEqual({
      answers: [{ question_id: 1, option_id: 11 }],
    });
    expect(result).toBeInstanceOf(Success);
    if (result instanceof Success) {
      expect(result.value.earned).toBe(3);
      expect(result.value.perQuestion[0].maxScore).toBe(2);
    }
  });
});
