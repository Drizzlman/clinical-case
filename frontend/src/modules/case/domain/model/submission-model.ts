export interface QuestionScoreModel {
  questionId: number;
  selectedOptionId: number;
  score: number;
  maxScore: number;
}

export interface SubmissionModel {
  id: number;
  caseId: number;
  earned: number;
  maximum: number;
  percentage: number;
  perQuestion: QuestionScoreModel[];
}
