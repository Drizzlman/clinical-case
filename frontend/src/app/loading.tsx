import type { FC } from "react";

const LoadingCases: FC = () => (
  <main className="mx-auto max-w-3xl p-4 sm:p-8" aria-busy="true">
    <div className="h-8 w-2/3 animate-pulse rounded bg-slate-200" />
    <div className="mt-2 h-4 w-1/3 animate-pulse rounded bg-slate-200" />
    <div className="mt-6 grid gap-4 sm:grid-cols-2">
      {[0, 1, 2, 3].map((index) => (
        <div key={index} className="h-36 animate-pulse rounded-xl bg-slate-200" />
      ))}
    </div>
  </main>
);

export default LoadingCases;
