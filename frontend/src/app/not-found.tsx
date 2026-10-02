import type { FC } from "react";
import Link from "next/link";

const NotFoundPage: FC = () => (
  <main className="mx-auto max-w-3xl p-4 sm:p-8">
    <h1 className="text-xl font-semibold">Page not found</h1>
    <p className="mt-2 text-slate-600">The page you are looking for does not exist.</p>
    <Link href="/" className="mt-4 inline-block font-medium text-brand-600 hover:underline">
      Back to cases
    </Link>
  </main>
);

export default NotFoundPage;
