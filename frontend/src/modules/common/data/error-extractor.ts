export function extractError(error: unknown): string {
  if (typeof error === "string") {
    return error;
  }
  if (error instanceof Error) {
    return error.message;
  }
  if (error !== null && typeof error === "object") {
    const record = error as Record<string, unknown>;
    if (typeof record.detail === "string") {
      return record.detail;
    }
    if (typeof record.title === "string") {
      return record.title;
    }
    if (typeof record.message === "string") {
      return record.message;
    }
  }
  return "Request failed";
}
