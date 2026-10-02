export interface SubmitAnswerDto {
  questionId: number;
  optionId: number;
}

export interface SubmitAnswersDto {
  caseId: number;
  answers: SubmitAnswerDto[];
}
