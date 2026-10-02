"use client";

import type { FC } from "react";

import { Button } from "@/modules/common/ui/Button";

const GlobalErrorPage: FC<{
  error: Error & { digest?: string };
  reset: () => void;
}> = ({ reset }) => (
  <main className="mx-auto max-w-3xl p-4 sm:p-8">
    <h1 className="text-xl font-semibold">Something went wrong</h1>
    <p className="mt-2 text-slate-600">We could not load this page. Please try again.</p>
    <div className="mt-4">
      <Button type="button" onClick={reset}>
        Try again
      </Button>
    </div>
  </main>
);

export default GlobalErrorPage;
