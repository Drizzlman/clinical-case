import type {
  CaseReadDto,
  CaseSummaryReadDto,
  SubmissionResultDto,
} from "@/modules/case/data/dto/case-dto";
import type { SubmitAnswersDto } from "@/modules/case/domain/dto/submit-answers-dto";
import { CaseDataMapper } from "@/modules/case/data/case-data-mapper";
import type { CaseModel } from "@/modules/case/domain/model/case-model";
import type { CaseSummaryModel } from "@/modules/case/domain/model/case-summary-model";
import type { SubmissionModel } from "@/modules/case/domain/model/submission-model";
import { resolveApiBaseUrl } from "@/modules/common/data/api-base-url";
import { extractError } from "@/modules/common/data/error-extractor";
import { Failure, Success, type OperationResult } from "@/modules/common/domain/operation-result";

async function readErrorMessage(response: Response): Promise<string> {
  try {
    return extractError(await response.json());
  } catch {
    return `Request failed with status ${response.status}`;
  }
}

export const CaseRepository = {
  async getCase(caseId: number): Promise<OperationResult<CaseModel>> {
    try {
      const response = await fetch(`${resolveApiBaseUrl()}/cases/${caseId}`, {
        cache: "no-store",
      });
      if (!response.ok) {
        return new Failure(await readErrorMessage(response), response.status);
      }
      const dto = (await response.json()) as CaseReadDto;
      return Success.from(CaseDataMapper.toCaseModel(dto));
    } catch (error) {
      return Failure.from(extractError(error));
    }
  },

  async listCases(): Promise<OperationResult<CaseSummaryModel[]>> {
    try {
      const response = await fetch(`${resolveApiBaseUrl()}/cases`, { cache: "no-store" });
      if (!response.ok) {
        return new Failure(await readErrorMessage(response), response.status);
      }
      const dto = (await response.json()) as CaseSummaryReadDto[];
      return Success.from(dto.map((item) => CaseDataMapper.toCaseSummaryModel(item)));
    } catch (error) {
      return Failure.from(extractError(error));
    }
  },

  async submitAnswers(dto: SubmitAnswersDto): Promise<OperationResult<SubmissionModel>> {
    try {
      const response = await fetch(`${resolveApiBaseUrl()}/cases/${dto.caseId}/submissions`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          answers: dto.answers.map((answer) => ({
            question_id: answer.questionId,
            option_id: answer.optionId,
          })),
        }),
      });
      if (!response.ok) {
        return new Failure(await readErrorMessage(response), response.status);
      }
      const body = (await response.json()) as SubmissionResultDto;
      return Success.from(CaseDataMapper.toSubmissionModel(body));
    } catch (error) {
      return Failure.from(extractError(error));
    }
  },
};
