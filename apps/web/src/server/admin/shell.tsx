import "server-only";
import type { ReactNode } from "react";
import { messages, type Locale } from "../../i18n/messages";
import type { AdminAccess } from "./access";
import { adminNavigation, type AdminNavigationItem } from "./navigation";
import { ThemeSelector } from "../../components/ThemeSelector";
// import { useSidebar } from "@/context/SidebarContext";
// import { Link } from "@/i18n/navigation";
import Image from "next/image";

const actionClass =
  "inline-block rounded-lg border border-teal-800 dark:border-teal-400 bg-white dark:bg-gray-900 px-5 py-3 font-semibold text-teal-900 dark:text-teal-200";

export function AdminFrame({
  locale,
  children,
}: {
  locale: Locale;
  children: ReactNode;
}) {
  const t = messages[locale];
  // const { isMobileOpen, toggleSidebar, toggleMobileSidebar } = useSidebar();
  return (
    <>
      <a href="#content" className="skip-link">
        {t.skip}
      </a>
      <header
        className="sticky top-0 z-99999 flex w-full border-gray-200 bg-white xl:border-b dark:border-gray-800 dark:bg-gray-900"
        //className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-6 px-6 py-8"
      >
        <div className="flex grow flex-col items-center justify-between xl:flex-row xl:px-6">
          <div className="flex w-full items-center justify-between gap-2 border-b border-gray-200 px-3 py-3 sm:gap-4 xl:justify-normal xl:border-b-0 xl:px-0 xl:py-4 dark:border-gray-800">
            <a href="/" className="xl:hidden">
              {/* <Image
              width={154}
              height={32}
              className="dark:hidden"
              src="/images/logo/logo.svg"
              alt="Logo"
            />
            <Image
              width={154}
              height={32}
              className="hidden dark:block"
              src="/images/logo/logo-dark.svg"
              alt="Logo"
            /> */}
              <div className="text-3xl font-bold tracking-tight">
                libris
                <span className="text-teal-700 dark:text-teal-300">.</span>
              </div>
            </a>

            <ThemeSelector locale={locale} />
          </div>
        </div>

        {/* <a href={`/${locale}`} className="text-3xl font-bold tracking-tight">
          libris<span className="text-teal-700 dark:text-teal-300">.</span>
        </a>
        <p className="font-semibold text-teal-900 dark:text-teal-200">{t.adminTitle}</p>
        <nav aria-label={t.languages} className="flex gap-5 text-sm">
          <a
            href="/pt/admin"
            hrefLang="pt-BR"
            aria-current={locale === "pt" ? "page" : undefined}
          >
            Português
          </a>
          <a
            href="/en/admin"
            hrefLang="en"
            aria-current={locale === "en" ? "page" : undefined}
          >
            English
          </a>
        </nav> */}
      </header>
      <main id="content" tabIndex={-1} className="mx-auto max-w-6xl px-6 pb-20">
        {children}
      </main>
      <footer className="border-t border-slate-200 dark:border-gray-700 px-6 py-8 text-center text-sm text-slate-600 dark:text-gray-400">
        {t.footer}
      </footer>
    </>
  );
}

function Logout({ locale, csrf }: { locale: Locale; csrf: string }) {
  return (
    <form action="/oidc/logout" method="post">
      <input type="hidden" name="csrf" value={csrf} />
      <input type="hidden" name="returnTo" value={`/${locale}`} />
      <button type="submit" className={actionClass}>
        {messages[locale].logout}
      </button>
    </form>
  );
}

export function AdminAccessState({
  locale,
  access,
  feedback,
}: {
  locale: Locale;
  access: Exclude<AdminAccess, { status: "authorized" }>;
  feedback?: string;
}) {
  const t = messages[locale];
  const description =
    access.status === "login_required"
      ? t.anonymous
      : access.status === "session_expired"
        ? t.expired
        : access.status === "service_unavailable"
          ? t.unavailable
          : access.status === "access_denied" &&
              access.reason === "api_forbidden"
            ? t.adminApiDenied
            : t.adminDenied;
  return (
    <section
      aria-labelledby="access-title"
      className="max-w-3xl rounded-2xl border border-slate-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-7"
    >
      <h1 id="access-title" className="text-3xl font-semibold">
        {t[access.status]}
      </h1>
      <p role="status" className="my-6 leading-relaxed">
        {description}
      </p>
      {feedback && (
        <p role="status" className="my-4">
          {feedback}
        </p>
      )}
      {access.status === "access_denied" && access.identity && (
        <p className="mb-6 break-words text-sm">
          {t.actor}: {access.identity.actor_id}
        </p>
      )}
      <div className="flex flex-wrap items-center gap-4">
        {(access.status === "login_required" ||
          access.status === "session_expired") && (
          <form action="/oidc/login" method="post">
            <input type="hidden" name="returnTo" value={`/${locale}/admin`} />
            <button type="submit" className={actionClass}>
              {t.login}
            </button>
          </form>
        )}
        {access.status === "service_unavailable" && (
          <a href={`/${locale}/admin`} className={actionClass}>
            {t.retry}
          </a>
        )}
        <a href={`/${locale}`} className={actionClass}>
          {t.backHome}
        </a>
        {access.csrf && <Logout locale={locale} csrf={access.csrf} />}
      </div>
    </section>
  );
}

export function AdminNavigation({
  locale,
  items,
}: {
  locale: Locale;
  items: readonly AdminNavigationItem[];
}) {
  const t = messages[locale];
  return (
    <nav
      aria-label={t.adminNavigation}
      className="rounded-2xl border border-slate-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6"
    >
      <ul className="space-y-4">
        <li>
          <a href={`/${locale}/admin`} aria-current="page">
            {t.adminOverview}
          </a>
        </li>
        {items.map((item) => (
          <li key={item.id}>
            <a href={item.href}>{item.label}</a>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export function AdminShell({
  locale,
  access,
}: {
  locale: Locale;
  access: Extract<AdminAccess, { status: "authorized" }>;
}) {
  const t = messages[locale];
  const items = adminNavigation(access.identity.permissions, locale);
  return (
    <div className="grid gap-8 md:grid-cols-[16rem_minmax(0,1fr)]">
      <AdminNavigation locale={locale} items={items} />
      <div className="min-w-0">
        <h1 className="text-3xl font-semibold sm:text-4xl">{t.adminTitle}</h1>
        <p className="my-6 max-w-2xl leading-relaxed text-slate-700 dark:text-gray-300">
          {t.adminDescription}
        </p>
        <p className="mb-6 break-words text-sm">
          {t.actor}: {access.identity.actor_id}
        </p>
        <Logout locale={locale} csrf={access.csrf} />
        <section aria-labelledby="capabilities-title" className="mt-10">
          <h2 id="capabilities-title" className="text-2xl font-semibold">
            {t.adminCapabilities}
          </h2>
          <p className="my-5 leading-relaxed text-slate-700 dark:text-gray-300">
            {t.adminNote}
          </p>
          {items.length === 0 ? (
            <p role="status">{t.adminEmpty}</p>
          ) : (
            <div className="grid gap-5 sm:grid-cols-2">
              {items.map((item) => (
                <section
                  key={item.id}
                  id={item.id}
                  aria-labelledby={`${item.id}-title`}
                  tabIndex={-1}
                  className="scroll-mt-6 rounded-2xl border border-slate-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6"
                >
                  <h3 id={`${item.id}-title`} className="text-xl font-semibold">
                    {item.label}
                  </h3>
                  <p className="mt-4 leading-relaxed text-slate-700 dark:text-gray-300">
                    {t.futureCapability}
                  </p>
                </section>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
