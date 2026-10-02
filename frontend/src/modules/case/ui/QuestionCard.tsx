import type { FC } from "react";

import type { QuestionModel } from "@/modules/case/domain/model/case-model";
import type { QuestionScoreModel } from "@/modules/case/domain/model/submission-model";
import { RadioOption } from "@/modules/common/ui/RadioOption";

interface QuestionCardProps {
  question: QuestionModel;
  index: number;
  selectedOptionId: number | undefined;
  isInvalid: boolean;
  review: QuestionScoreModel | null;
  onSelect: (optionId: number) => void;
}

export const QuestionCard: FC<QuestionCardProps> = ({
  question,
  index,
  selectedOptionId,
  isInvalid,
  review,
  onSelect,
}) => {
  const maxScore = review ? review.maxScore : null;
  const surfaceClass = isInvalid ? "border-red-400 bg-red-50" : "border-slate-200 bg-white";

  return (
    <fieldset
      id={`question-${question.id}`}
      tabIndex={-1}
      disabled={review !== null}
      aria-invalid={isInvalid}
      className={`rounded-xl border p-5 shadow-sm focus:outline-none ${surfaceClass}`}
    >
      <legend className="px-1 font-medium">
        {index + 1}. {question.text}
      </legend>
      <div className="mt-2 space-y-1">
        {question.options.map((option) => {
          const isCorrect = maxScore !== null && option.score === maxScore;
          const isSelected = selectedOptionId === option.id;
          const isWrongPick = review !== null && isSelected && !isCorrect;

          return (
            <RadioOption
              key={option.id}
              name={`question-${question.id}`}
              value={option.id}
              label={option.text}
              checked={isSelected}
              disabled={review !== null}
              tone={isCorrect ? "correct" : isWrongPick ? "incorrect" : "default"}
              statusLabel={isCorrect ? "Correct" : isWrongPick ? "Incorrect" : undefined}
              onSelect={onSelect}
            />
          );
        })}
      </div>
    </fieldset>
  );
};
