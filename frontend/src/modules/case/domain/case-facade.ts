import type { SubmitAnswersDto } from "@/modules/case/domain/dto/submit-answers-dto";
import type { SubmissionModel } from "@/modules/case/domain/model/submission-model";
import { submitAnswersUsecase } from "@/modules/case/domain/usecase/submit-answers.usecase";
import type { OperationResult } from "@/modules/common/domain/operation-result";

export const CaseFacade = {
  submitAnswers(dto: SubmitAnswersDto): Promise<OperationResult<SubmissionModel>> {
    return submitAnswersUsecase(dto);
  },
};
