import type { FC } from "react";

import type { QuestionModel } from "@/modules/case/domain/model/case-model";
import type { SubmissionModel } from "@/modules/case/domain/model/submission-model";
import { formatPercentage, formatScore, scoreBand } from "@/modules/case/ui/format";
import { Badge } from "@/modules/common/ui/Badge";
import { Button } from "@/modules/common/ui/Button";
import { Card } from "@/modules/common/ui/Card";
import { ProgressBar } from "@/modules/common/ui/ProgressBar";

const TONE_BY_BAND = {
  high: "success",
  medium: "warning",
  low: "danger",
} as const;

interface ResultPanelProps {
  questions: QuestionModel[];
  result: SubmissionModel;
  onReset: () => void;
}

export const ResultPanel: FC<ResultPanelProps> = ({ questions, result, onReset }) => {
  const percentage = result.percentage;
  const tone = TONE_BY_BAND[scoreBand(percentage)];
  const byId = new Map(questions.map((question) => [question.id, question]));

  return (
    <Card>
      <section aria-live="polite">
        <div className="flex items-center justify-between gap-4">
          <h2
            id="result-heading"
            tabIndex={-1}
            className="text-lg font-semibold focus:outline-none"
          >
            Result
          </h2>
          <Badge tone={tone}>{formatPercentage(result.percentage)}</Badge>
        </div>
        <p className="mt-1 text-sm text-slate-600">
          {formatScore(result.earned)} of {formatScore(result.maximum)} points
        </p>
        <div className="mt-3">
          <ProgressBar value={percentage} label="Score" />
        </div>
        <ul className="mt-4 space-y-3">
          {result.perQuestion.map((item) => {
            const question = byId.get(item.questionId);
            const selected = question?.options.find(
              (option) => option.id === item.selectedOptionId,
            );
            return (
              <li key={item.questionId} className="rounded-lg border border-slate-200 p-3 text-sm">
                <p className="font-medium">{question?.text ?? `Question ${item.questionId}`}</p>
                <p className="mt-1 text-slate-600">{selected?.text ?? "No answer recorded"}</p>
                <p className="mt-1 text-xs text-slate-500">
                  {formatScore(item.score)} / {formatScore(item.maxScore)} points
                </p>
              </li>
            );
          })}
        </ul>
        <div className="mt-4">
          <Button type="button" variant="secondary" onClick={onReset}>
            Take again
          </Button>
        </div>
      </section>
    </Card>
  );
};
