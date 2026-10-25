import Link from "next/link";

export default function ForbiddenPage() {
  return (
    <main className="mx-auto w-full max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-semibold">Acesso não autorizado</h1>
      <p className="mt-3 text-slate-600 dark:text-slate-300">
        Sua conta não possui as permissões necessárias para acessar esta área.
      </p>
      <Link
        href="/opac"
        className="mt-6 inline-flex font-semibold text-teal-700 hover:underline dark:text-teal-300"
      >
        Voltar ao catálogo
      </Link>
    </main>
  );
}
