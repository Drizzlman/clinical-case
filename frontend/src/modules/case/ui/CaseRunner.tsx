"use client";

import type { FC } from "react";

import type { QuestionModel } from "@/modules/case/domain/model/case-model";
import type { QuestionScoreModel } from "@/modules/case/domain/model/submission-model";
import { AttemptPanel } from "@/modules/case/ui/AttemptPanel";
import { QuestionCard } from "@/modules/case/ui/QuestionCard";
import { useCaseRunnerVm } from "@/modules/case/ui/use-case-runner-vm";

interface CaseRunnerProps {
  caseId: number;
  questions: QuestionModel[];
}

export const CaseRunner: FC<CaseRunnerProps> = ({ caseId, questions }) => {
  const vm = useCaseRunnerVm(caseId, questions);
  const reviewByQuestion = vm.result
    ? new Map<number, QuestionScoreModel>(
        vm.result.perQuestion.map((item) => [item.questionId, item]),
      )
    : null;

  return (
    <form
      className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem] lg:items-start"
      onSubmit={(event) => {
        event.preventDefault();
        vm.submit();
      }}
    >
      <div className="order-2 space-y-6 lg:order-1">
        {questions.map((question, index) => (
          <QuestionCard
            key={question.id}
            question={question}
            index={index}
            selectedOptionId={vm.answers[question.id]}
            isInvalid={vm.invalidIds.includes(question.id)}
            review={reviewByQuestion?.get(question.id) ?? null}
            onSelect={(optionId) => vm.selectOption(question.id, optionId)}
          />
        ))}
      </div>

      <aside className="order-1 lg:order-2 lg:sticky lg:top-6">
        <AttemptPanel
          questions={questions}
          answeredCount={vm.answeredCount}
          unanswered={vm.unanswered}
          status={vm.status}
          error={vm.error}
          result={vm.result}
          onJump={vm.jumpTo}
          onReset={vm.reset}
        />
      </aside>
    </form>
  );
};
