"use client";

import { useEffect, useState } from "react";

import { CaseFacade } from "@/modules/case/domain/case-facade";
import type { QuestionModel } from "@/modules/case/domain/model/case-model";
import type { SubmissionModel } from "@/modules/case/domain/model/submission-model";
import { Failure } from "@/modules/common/domain/operation-result";

export type CaseRunnerStatus = "idle" | "submitting" | "done";

export interface UnansweredQuestion {
  id: number;
  number: number;
}

export interface CaseRunnerVm {
  answers: Record<number, number>;
  status: CaseRunnerStatus;
  result: SubmissionModel | null;
  error: string | null;
  invalidIds: number[];
  unanswered: UnansweredQuestion[];
  answeredCount: number;
  selectOption: (questionId: number, optionId: number) => void;
  submit: () => void;
  reset: () => void;
  jumpTo: (questionId: number) => void;
}

export function useCaseRunnerVm(caseId: number, questions: QuestionModel[]): CaseRunnerVm {
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [status, setStatus] = useState<CaseRunnerStatus>("idle");
  const [result, setResult] = useState<SubmissionModel | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [invalidIds, setInvalidIds] = useState<number[]>([]);

  const unanswered = questions
    .map((question, index) => ({ id: question.id, number: index + 1 }))
    .filter(({ id }) => answers[id] === undefined);
  const answeredCount = questions.length - unanswered.length;

  useEffect(() => {
    if (invalidIds.length === 0) {
      return;
    }
    document.getElementById(`question-${invalidIds[0]}`)?.focus();
  }, [invalidIds]);

  useEffect(() => {
    if (result === null) {
      return;
    }
    document.getElementById("result-heading")?.focus();
  }, [result]);

  function selectOption(questionId: number, optionId: number): void {
    setAnswers((previous) => ({ ...previous, [questionId]: optionId }));
    setInvalidIds((previous) => previous.filter((id) => id !== questionId));
    setError(null);
  }

  function jumpTo(questionId: number): void {
    document.getElementById(`question-${questionId}`)?.focus();
  }

  function reset(): void {
    setAnswers({});
    setResult(null);
    setError(null);
    setInvalidIds([]);
    setStatus("idle");
  }

  async function runSubmit(): Promise<void> {
    if (unanswered.length > 0) {
      setInvalidIds(unanswered.map(({ id }) => id));
      setError(
        `Please answer question${unanswered.length === 1 ? "" : "s"} ${unanswered
          .map(({ number }) => number)
          .join(", ")} before submitting.`,
      );
      return;
    }

    setStatus("submitting");
    setError(null);
    const outcome = await CaseFacade.submitAnswers({
      caseId,
      answers: questions.map((question) => ({
        questionId: question.id,
        optionId: answers[question.id],
      })),
    });

    if (outcome instanceof Failure) {
      setError(outcome.message || "Submission failed. Please retry.");
      setStatus("idle");
      return;
    }

    setResult(outcome.value);
    setStatus("done");
  }

  function submit(): void {
    void runSubmit();
  }

  return {
    answers,
    status,
    result,
    error,
    invalidIds,
    unanswered,
    answeredCount,
    selectOption,
    submit,
    reset,
    jumpTo,
  };
}
