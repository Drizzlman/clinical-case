import type { FC } from "react";
import Link from "next/link";

import type { CaseSummaryModel } from "@/modules/case/domain/model/case-summary-model";
import { Card } from "@/modules/common/ui/Card";

interface CaseListProps {
  cases: CaseSummaryModel[];
}

export const CaseList: FC<CaseListProps> = ({ cases }) => (
  <ul className="grid gap-4 sm:grid-cols-2">
    {cases.map((clinicalCase) => (
      <li key={clinicalCase.id}>
        <Link href={`/cases/${clinicalCase.id}`} className="block h-full">
          <Card className="h-full transition-shadow hover:shadow-md">
            <h2 className="text-lg font-semibold">{clinicalCase.title}</h2>
            {clinicalCase.description ? (
              <p className="mt-1 text-sm text-slate-600">{clinicalCase.description}</p>
            ) : null}
            <p className="mt-3 text-xs font-medium uppercase tracking-wide text-slate-400">
              {clinicalCase.questionCount}{" "}
              {clinicalCase.questionCount === 1 ? "question" : "questions"}
            </p>
          </Card>
        </Link>
      </li>
    ))}
  </ul>
);
