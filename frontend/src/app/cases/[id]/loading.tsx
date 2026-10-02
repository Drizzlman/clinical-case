import type { FC } from "react";

const LoadingCase: FC = () => (
  <main className="mx-auto max-w-5xl p-4 sm:p-8" aria-busy="true">
    <div className="h-4 w-32 animate-pulse rounded bg-slate-200" />
    <div className="mt-4 h-8 w-1/2 animate-pulse rounded bg-slate-200" />
    <div className="mt-2 h-4 w-3/4 animate-pulse rounded bg-slate-200" />
    <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem] lg:items-start">
      <div className="order-2 space-y-6 lg:order-1">
        {[0, 1, 2].map((index) => (
          <div key={index} className="h-40 animate-pulse rounded-xl bg-slate-200" />
        ))}
      </div>
      <div className="order-1 space-y-4 lg:order-2">
        <div className="h-28 animate-pulse rounded-xl bg-slate-200" />
        <div className="h-11 animate-pulse rounded-md bg-slate-200" />
      </div>
    </div>
  </main>
);

export default LoadingCase;
