import { CaseRepository } from "@/modules/case/data/case-repository";
import type { SubmitAnswersDto } from "@/modules/case/domain/dto/submit-answers-dto";
import type { SubmissionModel } from "@/modules/case/domain/model/submission-model";
import type { OperationResult } from "@/modules/common/domain/operation-result";

export async function submitAnswersUsecase(
  dto: SubmitAnswersDto,
): Promise<OperationResult<SubmissionModel>> {
  return CaseRepository.submitAnswers(dto);
}
