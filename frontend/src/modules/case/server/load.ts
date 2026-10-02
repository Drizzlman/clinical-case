import { cache } from "react";

import type { CaseModel } from "@/modules/case/domain/model/case-model";
import type { CaseSummaryModel } from "@/modules/case/domain/model/case-summary-model";
import { getCaseUsecase } from "@/modules/case/domain/usecase/get-case.usecase";
import { listCasesUsecase } from "@/modules/case/domain/usecase/list-cases.usecase";
import { resolveMinimumLoadMs, withMinimumDelay } from "@/modules/common/data/min-delay";
import { Failure } from "@/modules/common/domain/operation-result";

export const loadCase = cache(async (caseId: number): Promise<CaseModel | null> => {
  const result = await withMinimumDelay(getCaseUsecase(caseId), resolveMinimumLoadMs());
  if (result instanceof Failure) {
    if (result.status === 404) {
      return null;
    }
    throw new Error(result.message);
  }
  return result.value;
});

export const loadCases = cache(async (): Promise<CaseSummaryModel[]> => {
  const result = await withMinimumDelay(listCasesUsecase(), resolveMinimumLoadMs());
  if (result instanceof Failure) {
    throw new Error(result.message);
  }
  return result.value;
});
