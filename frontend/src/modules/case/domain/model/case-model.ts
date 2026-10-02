export interface AnswerOptionModel {
  id: number;
  text: string;
  score: number;
  position: number;
}

export interface QuestionModel {
  id: number;
  text: string;
  kind: string;
  position: number;
  options: AnswerOptionModel[];
}

export interface CaseModel {
  id: number;
  title: string;
  description: string | null;
  questions: QuestionModel[];
}
