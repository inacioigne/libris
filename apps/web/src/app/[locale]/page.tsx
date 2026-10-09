import { Separator } from "@radix-ui/react-separator";
import Link from "next/link";
import { notFound } from "next/navigation";
import { isLocale, messages } from "@/i18n/messages";

export default async function Home({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const t = messages[locale];
  const foundations = [[t.semantic, t.semanticText], [t.modular, t.modularText], [t.accessible, t.accessibleText]];
  return <>
    <a href="#content" className="skip-link">{t.skip}</a>
    <header className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-6 px-6 py-8">
      <Link href={`/${locale}`} className="text-3xl font-bold tracking-tight">libris<span className="text-teal-700">.</span></Link>
      <nav aria-label={t.languages} className="flex gap-5 text-sm">
        <Link href="/pt" hrefLang="pt-BR" aria-current={locale === "pt" ? "page" : undefined}>Português</Link>
        <Link href="/en" hrefLang="en" aria-current={locale === "en" ? "page" : undefined}>English</Link>
      </nav>
    </header>
    <main id="content" className="mx-auto max-w-6xl px-6 pb-20 pt-12 sm:pt-20">
      <p className="mb-8 text-sm font-semibold uppercase tracking-widest text-teal-800">{t.stage}</p>
      <p className="mb-4 text-lg text-teal-800">{t.tagline}</p>
      <h1 className="max-w-4xl text-4xl font-semibold leading-tight tracking-tight sm:text-6xl">{t.title}</h1>
      <p className="mt-8 max-w-2xl text-lg leading-relaxed text-slate-700">{t.description}</p>
      <section aria-labelledby="foundations" className="mt-20">
        <h2 id="foundations" className="mb-6 text-xl font-semibold">{t.about}</h2>
        <div className="grid gap-5 md:grid-cols-3">{foundations.map(([title, text], index) =>
          <article key={title} className="rounded-2xl border border-slate-200 bg-white p-7">
            <span aria-hidden="true" className="text-sm font-medium text-teal-800">0{index + 1}</span>
            <h3 className="mb-3 mt-5 text-lg font-semibold">{title}</h3>
            <p className="leading-relaxed text-slate-700">{text}</p>
          </article>)}
        </div>
      </section>
      <p className="mt-10 max-w-3xl border-l-2 border-teal-700 pl-5 text-sm leading-relaxed text-slate-700">{t.note}</p>
    </main>
    <Separator decorative className="h-px bg-slate-200" />
    <footer className="px-6 py-8 text-center text-sm text-slate-600">{t.footer}</footer>
  </>;
}
