import { Suspense } from "react";

import { requestIdentity } from "@/lib/auth/request";


export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center"> 
    {/* bg-slate-950 px-6 py-12 text-slate-950" */}
      <section
        className="w-full max-w-md rounded-3xl bg-white p-8 shadow-2xl shadow-black/30 sm:p-10"
        aria-labelledby="login-title"
      >
        <h1 className="mb-3 text-sm font-semibold uppercase tracking-[0.22em] text-teal-700">
          Libris - Opac
        </h1>
      </section>
    </main>
  );
}
