export type OperationResult<T = void> = Success<T> | Failure;

export class Success<T> {
  private constructor(readonly value: T) {}

  static from<T>(value: T): Success<T> {
    return new Success(value);
  }
}

export class Failure {
  constructor(
    readonly message: string,
    readonly status?: number,
  ) {}

  static from(error: unknown): Failure {
    if (error instanceof Failure) {
      return error;
    }
    if (error instanceof Error) {
      return new Failure(error.message);
    }
    if (typeof error === "string") {
      return new Failure(error);
    }
    return new Failure("Unexpected error");
  }
}
