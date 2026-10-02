import type { FC } from "react";

import type { QuestionModel } from "@/modules/case/domain/model/case-model";
import type { SubmissionModel } from "@/modules/case/domain/model/submission-model";
import type { CaseRunnerStatus, UnansweredQuestion } from "@/modules/case/ui/use-case-runner-vm";
import { ResultPanel } from "@/modules/case/ui/ResultPanel";
import { Button } from "@/modules/common/ui/Button";
import { Card } from "@/modules/common/ui/Card";
import { ProgressBar } from "@/modules/common/ui/ProgressBar";

interface AttemptPanelProps {
  questions: QuestionModel[];
  answeredCount: number;
  unanswered: UnansweredQuestion[];
  status: CaseRunnerStatus;
  error: string | null;
  result: SubmissionModel | null;
  onJump: (questionId: number) => void;
  onReset: () => void;
}

export const AttemptPanel: FC<AttemptPanelProps> = ({
  questions,
  answeredCount,
  unanswered,
  status,
  error,
  result,
  onJump,
  onReset,
}) => (
  <div className="space-y-4">
    <Card>
      <div className="flex items-center justify-between text-sm text-slate-600">
        <span>
          Answered {answeredCount} of {questions.length}
        </span>
        {result ? <span className="font-medium text-emerald-600">Submitted</span> : null}
      </div>
      <div className="mt-2">
        <ProgressBar value={answeredCount} max={questions.length} label="Answered questions" />
      </div>

      {!result && unanswered.length > 0 ? (
        <div className="mt-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Unanswered</p>
          <ul className="mt-2 flex flex-wrap gap-2">
            {unanswered.map(({ id, number }) => (
              <li key={id}>
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  onClick={() => onJump(id)}
                  aria-label={`Go to question ${number}`}
                  className="rounded-full border border-slate-300 text-slate-600 hover:border-brand-500 hover:text-brand-600"
                >
                  {number}
                </Button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {error ? (
        <p role="alert" className="mt-4 text-sm font-medium text-red-600">
          {error}
        </p>
      ) : null}

      <div className="mt-4">
        {result ? null : (
          <Button type="submit" disabled={status === "submitting"} className="w-full">
            {status === "submitting" ? "Submitting…" : "Submit diagnosis"}
          </Button>
        )}
      </div>
    </Card>

    {result ? <ResultPanel questions={questions} result={result} onReset={onReset} /> : null}
  </div>
);
