import { requestIdentity } from "@/lib/auth/request";
import UserMenu from "./UserMenu";

export async function IdentityArea() {
  const identity = await requestIdentity();
  const returnTo = "/";

  if (!identity) {
    return (
      <form action="/oidc/login" method="post">
        <input type="hidden" name="returnTo" value={returnTo} />
        <button
          type="submit"
          className="cursor-pointer rounded-lg border border-teal-800 bg-white px-5 py-2 font-semibold text-teal-900 transition-colors hover:bg-teal-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-700 dark:border-teal-300 dark:bg-gray-900 dark:text-teal-300 dark:hover:bg-gray-800 dark:focus-visible:outline-teal-300"
        >
          Login
        </button>
      </form>
    );
  }

  return <UserMenu identity={identity} />

//   return (
//     <section aria-labelledby="user-information-title">
//       <h2
//         id="user-information-title"
//         className="text-2xl font-semibold text-slate-950"
//       >
//         Informações do usuário
//       </h2>
//       <code>{JSON.stringify(identity)}</code>
//       <form action="/oidc/logout" method="post">
//         <button type="submit">Sair</button>
//       </form>
//     </section>
//   );
}
