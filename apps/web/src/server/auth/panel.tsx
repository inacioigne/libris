import "server-only";
import { messages, type Locale } from "@/i18n/messages";
import { requestIdentity } from "./request";

export async function AuthPanel({
  locale,
  searchParams,
}: {
  locale: Locale;
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const t = messages[locale];
  const result = await requestIdentity();

  const query = new URLSearchParams();
  // Preserve ordinary page context, excluding authentication feedback.
  for (const [key, value] of Object.entries(searchParams)) {
    if (key === "auth" || value === undefined) continue;
    for (const item of Array.isArray(value) ? value : [value])
      query.append(key, item);
  }
  const returnTo = `/${locale}${query.size ? `?${query}` : ""}`;
  const feedback =
    searchParams.auth === "cancelled"
      ? t.cancelled
      : searchParams.auth === "error"
        ? t.authError
        : undefined;
  const statusText = {
    authenticated: t.authenticated,
    anonymous: t.anonymous,
    expired: t.expired,
    forbidden: t.forbidden,
    unavailable: t.unavailable,
  }[result.status];
  const buttonClass =
    "rounded-lg border border-teal-800 dark:border-teal-400 bg-white dark:bg-gray-900 px-5 py-3 font-semibold text-teal-900 dark:text-teal-200";
  return (
    <section
      aria-labelledby="auth-title"
      className="mt-10 max-w-3xl rounded-2xl border border-slate-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-7"
    >
      <h2 id="auth-title" className="text-xl font-semibold">
        {t.authTitle}
      </h2>
      <p role="status" className="my-4">
        {feedback ?? statusText}
      </p>
      {result.status === "authenticated" && (
        <>
          <p>{t.authenticated}</p>
          <dl className="my-4 break-words text-sm">
            <dt className="font-semibold">{t.actor}</dt>
            <dd>{result.identity.actor_id}</dd>
            <dt className="mt-3 font-semibold">{t.roles}</dt>
            <dd>{result.identity.roles.join(", ") || t.noPermissions}</dd>
            <dt className="mt-3 font-semibold">{t.permissions}</dt>
            <dd>{result.identity.permissions.join(", ") || t.noPermissions}</dd>
          </dl>
        </>
      )}
      {result.csrf ? (
        <form action="/oidc/logout" method="post">
          <input type="hidden" name="csrf" value={result.csrf} />
          <input type="hidden" name="returnTo" value={`/${locale}`} />
          <button type="submit" className={buttonClass}>
            {t.logout}
          </button>
        </form>
      ) : (
        <form action="/oidc/login" method="post">
          <input type="hidden" name="returnTo" value={returnTo} />
          <button type="submit" className={buttonClass}>
            {t.login}
          </button>
        </form>
      )}
    </section>
  );
}
