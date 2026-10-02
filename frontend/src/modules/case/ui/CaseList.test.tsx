import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { CaseSummaryModel } from "@/modules/case/domain/model/case-summary-model";

import { CaseList } from "./CaseList";

const cases: CaseSummaryModel[] = [
  { id: 1, title: "Acute Chest Pain", description: "Chest pain", questionCount: 3 },
  { id: 2, title: "Pediatric Fever", description: null, questionCount: 1 },
];

describe("CaseList", () => {
  it("links each case to its page", () => {
    render(<CaseList cases={cases} />);

    expect(screen.getByRole("link", { name: /Acute Chest Pain/ })).toHaveAttribute(
      "href",
      "/cases/1",
    );
    expect(screen.getByRole("link", { name: /Pediatric Fever/ })).toHaveAttribute(
      "href",
      "/cases/2",
    );
  });

  it("shows the question count with correct pluralization", () => {
    render(<CaseList cases={cases} />);

    expect(screen.getByText(/3 questions/)).toBeInTheDocument();
    expect(screen.getByText(/1 question$/)).toBeInTheDocument();
  });
});
