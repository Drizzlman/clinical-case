import type {
  CaseReadDto,
  CaseSummaryReadDto,
  QuestionReadDto,
  SubmissionResultDto,
} from "@/modules/case/data/dto/case-dto";
import type {
  AnswerOptionModel,
  CaseModel,
  QuestionModel,
} from "@/modules/case/domain/model/case-model";
import type { CaseSummaryModel } from "@/modules/case/domain/model/case-summary-model";
import type {
  QuestionScoreModel,
  SubmissionModel,
} from "@/modules/case/domain/model/submission-model";

export const CaseDataMapper = {
  toCaseModel(dto: CaseReadDto): CaseModel {
    return {
      id: dto.id,
      title: dto.title,
      description: dto.description ?? null,
      questions: dto.questions.map(
        (question: QuestionReadDto): QuestionModel => ({
          id: question.id,
          text: question.text,
          kind: question.kind,
          position: question.position,
          options: question.options.map(
            (option): AnswerOptionModel => ({
              id: option.id,
              text: option.text,
              score: Number(option.score),
              position: option.position,
            }),
          ),
        }),
      ),
    };
  },

  toCaseSummaryModel(dto: CaseSummaryReadDto): CaseSummaryModel {
    return {
      id: dto.id,
      title: dto.title,
      description: dto.description ?? null,
      questionCount: dto.question_count,
    };
  },

  toSubmissionModel(dto: SubmissionResultDto): SubmissionModel {
    return {
      id: dto.id,
      caseId: dto.case_id,
      earned: Number(dto.earned),
      maximum: Number(dto.maximum),
      percentage: Number(dto.percentage),
      perQuestion: dto.per_question.map(
        (item): QuestionScoreModel => ({
          questionId: item.question_id,
          selectedOptionId: item.selected_option_id,
          score: Number(item.score),
          maxScore: Number(item.max_score),
        }),
      ),
    };
  },
};
