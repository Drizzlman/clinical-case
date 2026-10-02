import { CaseRepository } from "@/modules/case/data/case-repository";
import type { CaseSummaryModel } from "@/modules/case/domain/model/case-summary-model";
import type { OperationResult } from "@/modules/common/domain/operation-result";

export async function listCasesUsecase(): Promise<OperationResult<CaseSummaryModel[]>> {
  return CaseRepository.listCases();
}
