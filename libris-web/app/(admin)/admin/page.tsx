import { Suspense } from "react";
import { redirect } from "next/navigation";

import { requestIdentity } from "@/lib/auth/request";

async function IdentityDetails() {
  const identity = await requestIdentity();

  if (!identity) {
    redirect("/login");
  }

  return (
    <dl className="mt-5 space-y-5">
      <div>
        <dt className="text-sm font-medium text-slate-600">Identificador</dt>
        <dd className="mt-1 break-all font-mono text-sm text-slate-950">
          {identity.actorId}
        </dd>
      </div>
      <div>
        <dt className="text-sm font-medium text-slate-600">Papéis</dt>
        <dd className="mt-1 text-slate-950">
          {identity.roles.length > 0
            ? identity.roles.join(", ")
            : "Nenhum papel atribuído"}
        </dd>
      </div>
      <div>
        <dt className="text-sm font-medium text-slate-600">Permissões</dt>
        <dd className="mt-1 text-slate-950">
          {identity.permissions.length > 0
            ? identity.permissions.join(", ")
            : "Nenhuma permissão atribuída"}
        </dd>
      </div>
    </dl>
  );
}

export default function Home() {
  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-teal-700">
            Libris
          </p>
          <h1 className="mt-3 text-3xl font-semibold">Área administrativa</h1>
          <p className="mt-3 text-slate-600">Sessão autenticada com sucesso.</p>
        </div>

        <section
          className="my-10 w-full rounded-2xl border border-slate-200 bg-slate-50 p-6"
          aria-labelledby="identity-title"
        >
          <h2 id="identity-title" className="text-xl font-semibold">
            Informações do usuário
          </h2>

          <Suspense
            fallback={
              <p className="mt-5 text-sm text-slate-600" role="status">
                Carregando informações do usuário...
              </p>
            }
          >
            <IdentityDetails />
          </Suspense>
        </section>
      </main>
    </div>
  );
}
