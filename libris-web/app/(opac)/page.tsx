import Link from "next/link";

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

        <form action="/oidc/login" method="post">
          <input type="hidden" name="returnTo" value="/admin" />
          <button
            type="submit"
            className="w-full cursor-pointer rounded-xl bg-teal-700 px-5 py-3.5 font-semibold text-white transition hover:bg-teal-800 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-teal-700"
          >
            Entrar com Libris
          </button>
        </form>
      </section>
    </main>
  );
}
