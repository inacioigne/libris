import { Suspense } from "react";

import { requestIdentity } from "@/lib/auth/request";

async function IdentityArea() {
  const identity = await requestIdentity();
  const returnTo = "/";

  if (!identity) {
    return (
      <form action="/oidc/login" method="post">
        <input type="hidden" name="returnTo" value={returnTo} />
        <button
          type="submit"
          className="w-full cursor-pointer rounded-xl bg-teal-700 px-5 py-3.5 font-semibold text-white transition hover:bg-teal-800 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-teal-700"
        >
          Entrar com Libris
        </button>
      </form>
    );
  }

  return (
    <section aria-labelledby="user-information-title">
      <h2
        id="user-information-title"
        className="text-2xl font-semibold text-slate-950"
      >
        Informações do usuário
      </h2>
      <dl className="mt-5 space-y-4">
        <div>
          <dt className="text-sm font-medium text-slate-600">Identificador</dt>
          <dd className="mt-1 break-all font-mono text-sm">
            {identity.actorId}
          </dd>
        </div>
        <div>
          <dt className="text-sm font-medium text-slate-600">Papéis</dt>
          <dd className="mt-1">
            {identity.roles.length > 0
              ? identity.roles.join(", ")
              : "Nenhum papel atribuído"}
          </dd>
        </div>
        <div>
          <dt className="text-sm font-medium text-slate-600">Permissões</dt>
          <dd className="mt-1">
            {identity.permissions.length > 0
              ? identity.permissions.join(", ")
              : "Nenhuma permissão atribuída"}
          </dd>
        </div>
      </dl>
    </section>
  );
}

export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 py-12 text-slate-950">
      <section
        className="w-full max-w-md rounded-3xl bg-white p-8 shadow-2xl shadow-black/30 sm:p-10"
        aria-labelledby="login-title"
      >
        <h1 className="mb-3 text-sm font-semibold uppercase tracking-[0.22em] text-teal-700">
          Libris - Opac
        </h1>

        <Suspense
          fallback={
            <p className="text-sm text-slate-600" role="status">
              Verificando sessão...
            </p>
          }
        >
          <IdentityArea />
        </Suspense>
      </section>
    </main>
  );
}
