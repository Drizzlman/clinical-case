"use client";

import type { FC } from "react";

import { Button } from "@/modules/common/ui/Button";

const CaseError: FC<{
  error: Error & { digest?: string };
  reset: () => void;
}> = ({ reset }) => (
  <main className="mx-auto max-w-3xl p-4 sm:p-8">
    <h1 className="text-xl font-semibold">Could not load the case</h1>
    <p className="mt-2 text-slate-600">Something went wrong while loading this case.</p>
    <div className="mt-4">
      <Button type="button" onClick={reset}>
        Retry
      </Button>
    </div>
  </main>
);

export default CaseError;
