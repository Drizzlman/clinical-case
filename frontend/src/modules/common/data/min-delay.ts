const DEFAULT_MIN_LOAD_MS = 2000;

export function resolveMinimumLoadMs(): number {
  const raw = process.env.MIN_PAGE_LOAD_MS;
  if (raw === undefined) {
    return DEFAULT_MIN_LOAD_MS;
  }
  const parsed = Number(raw);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : DEFAULT_MIN_LOAD_MS;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function withMinimumDelay<T>(task: Promise<T>, ms: number): Promise<T> {
  if (ms <= 0) {
    return task;
  }
  const [value] = await Promise.all([task, sleep(ms)]);
  return value;
}
