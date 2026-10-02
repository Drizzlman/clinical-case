import { describe, expect, it } from "vitest";

import { formatPercentage, formatScore, scoreBand } from "./format";

describe("formatScore", () => {
  it("drops trailing zeros from Decimal strings", () => {
    expect(formatScore("30.0000")).toBe("30");
    expect(formatScore("56.67")).toBe("56.67");
    expect(formatScore(100)).toBe("100");
  });

  it("returns the raw value when it is not numeric", () => {
    expect(formatScore("n/a")).toBe("n/a");
  });
});

describe("formatPercentage", () => {
  it("appends a percent sign", () => {
    expect(formatPercentage("56.67")).toBe("56.67%");
  });
});

describe("scoreBand", () => {
  it("bands percentages into low, medium, and high", () => {
    expect(scoreBand(100)).toBe("high");
    expect(scoreBand(60)).toBe("medium");
    expect(scoreBand(10)).toBe("low");
  });
});
