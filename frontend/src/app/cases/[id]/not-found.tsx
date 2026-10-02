import type { FC } from "react";
import Link from "next/link";

const CaseNotFound: FC = () => (
  <main className="mx-auto max-w-3xl p-4 sm:p-8">
    <h1 className="text-xl font-semibold">Case not found</h1>
    <p className="mt-2 text-slate-600">The requested case does not exist.</p>
    <Link href="/" className="mt-4 inline-block font-medium text-brand-600 hover:underline">
      Back to cases
    </Link>
  </main>
);

export default CaseNotFound;
