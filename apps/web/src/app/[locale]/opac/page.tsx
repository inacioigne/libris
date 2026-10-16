import { Separator } from "@radix-ui/react-separator";
import Link from "next/link";
import { notFound } from "next/navigation";
import { AuthPanel } from "@/server/auth/panel";
import { isLocale, messages } from "@/i18n/messages";
// import { AppHeader } from "@/layout/opac/AppHeader";

export const dynamic = "force-dynamic";
export default async function Home({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const t = messages[locale];
  const foundations = [
    [t.semantic, t.semanticText],
    [t.modular, t.modularText],
    [t.accessible, t.accessibleText],
  ];
  return (
    <>
      <a href="#content" className="skip-link">
        {t.skip}
      </a>
      {/* <header className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-6 px-6 py-8">
        <Link href={`/${locale}`} className="text-3xl font-bold tracking-tight">
          libris<span className="text-teal-700 dark:text-teal-300">.</span>
        </Link>
        <nav aria-label={t.languages} className="flex gap-5 text-sm">
          <Link
            href="/pt"
            hrefLang="pt-BR"
            aria-current={locale === "pt" ? "page" : undefined}
          >
            Português
          </Link>
          <Link
            href="/en"
            hrefLang="en"
            aria-current={locale === "en" ? "page" : undefined}
          >
            English
          </Link>
        </nav>
        <ThemeSelector locale={locale} />
      </header> */}
      {/* <AppHeader /> */}
      <main
        id="content"
        className="mx-auto max-w-6xl px-6 pb-20 pt-12 sm:pt-20"
      >
        <p className="mb-8 text-sm font-semibold uppercase tracking-widest text-teal-800 dark:text-teal-300">
          {t.stage}
        </p>
        <p className="mb-4 text-lg text-teal-800 dark:text-teal-300">{t.tagline}</p>
        <h1 className="max-w-4xl text-4xl font-semibold leading-tight tracking-tight sm:text-6xl">
          {t.title}
        </h1>
        <p className="mt-8 max-w-2xl text-lg leading-relaxed text-slate-700 dark:text-gray-300">
          {t.description}
        </p>
        <AuthPanel locale={locale} searchParams={await searchParams} />
        <p className="mt-6"><Link href={`/${locale}/admin`} className="font-semibold text-teal-900 dark:text-teal-200">{t.adminTitle}</Link></p>
        <section aria-labelledby="foundations" className="mt-20">
          <h2 id="foundations" className="mb-6 text-xl font-semibold">
            {t.about}
          </h2>
          <div className="grid gap-5 md:grid-cols-3">
            {foundations.map(([title, text], index) => (
              <article
                key={title}
                className="rounded-2xl border border-slate-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-7"
              >
                <span
                  aria-hidden="true"
                  className="text-sm font-medium text-teal-800 dark:text-teal-300"
                >
                  0{index + 1}
                </span>
                <h3 className="mb-3 mt-5 text-lg font-semibold">{title}</h3>
                <p className="leading-relaxed text-slate-700 dark:text-gray-300">{text}</p>
              </article>
            ))}
          </div>
        </section>
        <p className="mt-10 max-w-3xl border-l-2 border-teal-700 dark:border-teal-400 pl-5 text-sm leading-relaxed text-slate-700 dark:text-gray-300">
          {t.note}
        </p>
      </main>
      <Separator decorative className="h-px bg-slate-200 dark:bg-gray-700" />
      <footer className="px-6 py-8 text-center text-sm text-slate-600 dark:text-gray-400">
        {t.footer}
      </footer>
    </>
  );
}
