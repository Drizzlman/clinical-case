import type { ReactElement } from "react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { CaseRunner } from "@/modules/case/ui/CaseRunner";
import { loadCase } from "@/modules/case/server/load";

interface CasePageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: CasePageProps): Promise<Metadata> {
  const { id } = await params;
  const caseId = Number(id);
  if (!Number.isInteger(caseId)) {
    return { title: "Case not found" };
  }
  const clinicalCase = await loadCase(caseId);
  return { title: clinicalCase ? clinicalCase.title : "Case not found" };
}

export default async function CasePage({ params }: CasePageProps): Promise<ReactElement> {
  const { id } = await params;
  const caseId = Number(id);
  if (!Number.isInteger(caseId)) {
    notFound();
  }

  const clinicalCase = await loadCase(caseId);
  if (clinicalCase === null) {
    notFound();
  }

  return (
    <main className="mx-auto max-w-5xl p-4 sm:p-8">
      <nav aria-label="Breadcrumb" className="mb-4 text-sm text-slate-500">
        <Link href="/" className="hover:text-slate-900 hover:underline">
          Cases
        </Link>
        <span className="mx-1.5">/</span>
        <span className="text-slate-700">{clinicalCase.title}</span>
      </nav>
      <h1 className="text-2xl font-semibold">{clinicalCase.title}</h1>
      {clinicalCase.description ? (
        <p className="mt-2 text-slate-600">{clinicalCase.description}</p>
      ) : null}
      <CaseRunner caseId={clinicalCase.id} questions={clinicalCase.questions} />
    </main>
  );
}
