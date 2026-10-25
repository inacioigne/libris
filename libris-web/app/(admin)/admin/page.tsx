import {
  adminPermission,
  requireAdminPageAccess,
} from "../page-access";

function IdentityDetails({
  identity,
}: {
  identity: Awaited<ReturnType<typeof requireAdminPageAccess>>["identity"];
}) {
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

export default async function Home() {
  // const { identity } = await requireAdminPageAccess(
  //   { allOf: [adminPermission.systemAdmin] },
  //   "/admin",
  // );

  return (
    <main className="flex w-full max-w-3xl flex-1 flex-col items-center justify-between bg-white px-16 py-32 dark:bg-black sm:items-start">
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

        {/* <IdentityDetails identity={identity} /> */}
      </section>
    </main>
  );
}
