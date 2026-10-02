import type { ReactElement } from "react";

import { CaseList } from "@/modules/case/ui/CaseList";
import { loadCases } from "@/modules/case/server/load";

export const dynamic = "force-dynamic";

export default async function HomePage(): Promise<ReactElement> {
  const cases = await loadCases();

  return (
    <main className="mx-auto max-w-3xl p-4 sm:p-8">
      <header>
        <h1 className="text-2xl font-semibold">Clinical Case Scoring Platform</h1>
        <p className="mt-2 text-slate-600">Choose a clinical case to take.</p>
      </header>
      <section className="mt-6">
        {cases.length === 0 ? (
          <p className="rounded-lg border border-dashed border-slate-300 p-6 text-center text-slate-500">
            No cases yet. Load the default data or create a case through the API.
          </p>
        ) : (
          <CaseList cases={cases} />
        )}
      </section>
    </main>
  );
}
