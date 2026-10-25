import Link from "next/link";

export default function AdminUnavailablePage() {
  return (
    <main className="mx-auto w-full max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-semibold">
        Área administrativa indisponível
      </h1>
      <p className="mt-3 text-slate-600 dark:text-slate-300">
        Não foi possível verificar suas permissões agora. Tente novamente em
        instantes.
      </p>
      <Link
        href="/admin"
        className="mt-6 inline-flex font-semibold text-teal-700 hover:underline dark:text-teal-300"
      >
        Tentar novamente
      </Link>
    </main>
  );
}
