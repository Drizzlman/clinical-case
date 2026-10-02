export function formatScore(value: string | number): string {
  const numeric = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numeric)) {
    return String(value);
  }
  return numeric.toLocaleString("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
}

export function formatPercentage(value: string | number): string {
  return `${formatScore(value)}%`;
}

export type ScoreBand = "low" | "medium" | "high";

export function scoreBand(percentage: number): ScoreBand {
  if (percentage >= 80) {
    return "high";
  }
  if (percentage >= 50) {
    return "medium";
  }
  return "low";
}
