import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Entrar | Libris",
  description: "Acesso seguro ao ambiente administrativo do Libris.",
};

const ERROR_MESSAGES: Record<string, string> = {
  access_denied: "O acesso foi cancelado. Você pode tentar novamente.",
  authentication_failed:
    "Não foi possível concluir a autenticação. Tente novamente.",
  invalid_callback:
    "A solicitação de acesso expirou ou é inválida. Inicie o acesso novamente.",
};

type LoginPageProps = {
  searchParams: Promise<{ error?: string | string[] }>;
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const { error } = await searchParams;
  const errorCode = typeof error === "string" ? error : undefined;
  const errorMessage = errorCode ? ERROR_MESSAGES[errorCode] : undefined;

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 py-12 text-slate-950">
      <section
        className="w-full max-w-md rounded-3xl bg-white p-8 shadow-2xl shadow-black/30 sm:p-10"
        aria-labelledby="login-title"
      >
        <div className="mb-8">
          <p className="mb-3 text-sm font-semibold uppercase tracking-[0.22em] text-teal-700">
            Libris
          </p>
          <h1 id="login-title" className="text-3xl font-semibold tracking-tight">
            Acesso da equipe
          </h1>
          <p className="mt-3 leading-7 text-slate-600">
            Entre com sua conta institucional para acessar catalogação e os
            demais serviços administrativos.
          </p>
        </div>

        {errorMessage ? (
          <p
            className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-800"
            role="alert"
          >
            {errorMessage}
          </p>
        ) : null}

        <form action="/oidc/login" method="post">
          <input type="hidden" name="returnTo" value="/admin" />
          <button
            type="submit"
            className="w-full cursor-pointer rounded-xl bg-teal-700 px-5 py-3.5 font-semibold text-white transition hover:bg-teal-800 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-teal-700"
          >
            Entrar com Libris
          </button>
        </form>

        <p className="mt-5 text-center text-sm leading-6 text-slate-500">
          Você será direcionado ao serviço seguro de identidade da instituição.
        </p>

        <div className="mt-8 border-t border-slate-200 pt-6 text-center">
          <Link
            href="/"
            className="font-medium text-teal-700 underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-teal-700"
          >
            Voltar ao catálogo público
          </Link>
        </div>
      </section>
    </main>
  );
}
