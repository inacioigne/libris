import "server-only";
import type { ReactNode } from "react";
import { messages, type Locale } from "../../i18n/messages";
import type { AdminAccess } from "./access";
import { adminNavigation, type AdminNavigationItem } from "./navigation";

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

  return (
    <>
      <a href="#content" className="skip-link">
        {t.skip}
      </a>

      <main id="content" tabIndex={-1} className="mx-auto max-w-7xl px-6 py-10">
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
      <input type="hidden" name="returnTo" value={`/${locale}/opac`} />
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
        <p className="mb-6 wrap-break-word text-sm">
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
        <a href={`/${locale}/opac`} className={actionClass}>
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
        <p className="mb-6 wrap-break-word text-sm">
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
