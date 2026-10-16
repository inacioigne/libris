import { requestIdentity } from "@/server/auth/request";
import { messages, type Locale } from "@/i18n/messages";
import UserDropdown from "./UserDropdown";

export default async function UserArea({ locale }: { locale: Locale }) {
  const t = messages[locale];
  const result = await requestIdentity();
  const returnTo = `/${locale}/opac`;

  

  if (result.status === "authenticated")  {
    return <UserDropdown locale={locale} result={result} />;
  } else {
    return (
      <form action="/oidc/login" method="post">
        <input type="hidden" name="returnTo" value={returnTo} />
        <button
          type="submit"
          className="rounded-lg border border-teal-800 dark:border-teal-400 bg-white dark:bg-gray-900 px-5 py-2 font-semibold text-teal-900 dark:text-teal-200 cursor-pointer"
        >
          {t.login}
        </button>
      </form>
    );
  }
}
