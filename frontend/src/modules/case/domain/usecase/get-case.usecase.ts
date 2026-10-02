import { CaseRepository } from "@/modules/case/data/case-repository";
import type { CaseModel } from "@/modules/case/domain/model/case-model";
import type { OperationResult } from "@/modules/common/domain/operation-result";

export async function getCaseUsecase(caseId: number): Promise<OperationResult<CaseModel>> {
  return CaseRepository.getCase(caseId);
}
