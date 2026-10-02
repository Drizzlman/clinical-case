import { afterEach, describe, expect, it } from "vitest";

import { resolveMinimumLoadMs, withMinimumDelay } from "./min-delay";

afterEach(() => {
  delete process.env.MIN_PAGE_LOAD_MS;
});

describe("resolveMinimumLoadMs", () => {
  it("defaults to 2000", () => {
    expect(resolveMinimumLoadMs()).toBe(2000);
  });

  it("reads a configured value", () => {
    process.env.MIN_PAGE_LOAD_MS = "0";
    expect(resolveMinimumLoadMs()).toBe(0);
  });

  it("falls back to the default on an invalid value", () => {
    process.env.MIN_PAGE_LOAD_MS = "not-a-number";
    expect(resolveMinimumLoadMs()).toBe(2000);
  });
});

describe("withMinimumDelay", () => {
  it("returns the task result without waiting when ms <= 0", async () => {
    await expect(withMinimumDelay(Promise.resolve("ok"), 0)).resolves.toBe("ok");
  });

  it("waits at least the configured minimum", async () => {
    const start = Date.now();
    await expect(withMinimumDelay(Promise.resolve("ok"), 60)).resolves.toBe("ok");
    expect(Date.now() - start).toBeGreaterThanOrEqual(50);
  });

  it("does not add the delay on top of a slower task", async () => {
    const start = Date.now();
    const slow = new Promise<string>((resolve) => setTimeout(() => resolve("ok"), 50));
    await withMinimumDelay(slow, 10);
    expect(Date.now() - start).toBeLessThan(200);
  });

  it("propagates a task rejection", async () => {
    const failing = Promise.reject(new Error("boom"));
    await expect(withMinimumDelay(failing, 0)).rejects.toThrow("boom");
  });
});
