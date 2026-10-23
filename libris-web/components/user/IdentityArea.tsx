import { requestIdentity } from "@/lib/auth/request";

export async function IdentityArea() {
  const identity = await requestIdentity();
  const returnTo = "/";

  if (!identity) {
    return (
      <form action="/oidc/login" method="post">
        <input type="hidden" name="returnTo" value={returnTo} />
        <button
          type="submit"
          className=" cursor-pointer rounded-lg border border-teal-800  bg-white px-5 py-2 font-semibold text-teal-900"
        >
          Login
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
      <code>{JSON.stringify(identity)}</code>
      {/* <dl className="mt-5 space-y-4">
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
      </dl> */}
    </section>
  );
}