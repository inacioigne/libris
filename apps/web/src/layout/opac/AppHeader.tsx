import { ThemeToggleButton } from "@/components/shared/ThemeToggleButton";
import { messages, type Locale } from "@/i18n/messages";
import Link from "next/link";
import { requestIdentity } from "@/server/auth/request";
import UserDropdown from "@/components/header/UserDropdown";
import UserArea from "@/components/header/UserArea";

export default async function AppHeader({ locale }: { locale: Locale }) {
  const t = messages[locale];
  const result = await requestIdentity();

  const returnTo = `/${locale}/opac`;

  const buttonClass =
    "rounded-lg border border-teal-800 dark:border-teal-400 bg-white dark:bg-gray-900 px-5 py-2 font-semibold text-teal-900 dark:text-teal-200 cursor-pointer";

  return (
    <header className="sticky top-0 z-99999 flex w-full border-gray-200 bg-white xl:border-b dark:border-gray-800 dark:bg-gray-900">
      <div className="flex grow flex-col items-center justify-between xl:flex-row xl:px-6">
        <div className="flex w-full items-center justify-between gap-2 border-b border-gray-200 px-3 py-3 sm:gap-4 xl:justify-normal xl:border-b-0 xl:px-0 xl:py-4 dark:border-gray-800">
          <Link href={`/${locale}/opac`} className="xl:hidden">
            <div className="text-3xl font-bold tracking-tight">
              libris
              <span className="text-teal-700 dark:text-teal-300">.</span>
            </div>
          </Link>

          <div className="hidden xl:block">
            <form>
              <div className="relative">
                <span className="inset-s-4 pointer-events-none absolute top-1/2 -translate-y-1/2">
                  <svg
                    className="fill-gray-500 dark:fill-gray-400"
                    width="20"
                    height="20"
                    viewBox="0 0 20 20"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      fillRule="evenodd"
                      clipRule="evenodd"
                      d="M3.04175 9.37363C3.04175 5.87693 5.87711 3.04199 9.37508 3.04199C12.8731 3.04199 15.7084 5.87693 15.7084 9.37363C15.7084 12.8703 12.8731 15.7053 9.37508 15.7053C5.87711 15.7053 3.04175 12.8703 3.04175 9.37363ZM9.37508 1.54199C5.04902 1.54199 1.54175 5.04817 1.54175 9.37363C1.54175 13.6991 5.04902 17.2053 9.37508 17.2053C11.2674 17.2053 13.003 16.5344 14.357 15.4176L17.177 18.238C17.4699 18.5309 17.9448 18.5309 18.2377 18.238C18.5306 17.9451 18.5306 17.4703 18.2377 17.1774L15.418 14.3573C16.5365 13.0033 17.2084 11.2669 17.2084 9.37363C17.2084 5.04817 13.7011 1.54199 9.37508 1.54199Z"
                      fill=""
                    />
                  </svg>
                </span>
                <input
                  // ref={inputRef}
                  type="text"
                  // placeholder={t("searchPlaceholder")}
                  className="dark:bg-dark-900 h-11 w-full rounded-lg border border-gray-200 bg-transparent py-2.5 ps-12 pe-14 text-sm text-gray-800 shadow-theme-xs placeholder:text-gray-400 focus:border-brand-300 focus:ring-3 focus:ring-brand-500/10 focus:outline-hidden xl:w-107.5 dark:border-gray-800 dark:bg-white/3 dark:text-white/90 dark:placeholder:text-white/30 dark:focus:border-brand-800"
                />
                <button className="inset-e-2.5 absolute top-1/2 inline-flex -translate-y-1/2 items-center gap-0.5 rounded-lg border border-gray-200 bg-gray-50 px-1.75 py-[4.5px] text-xs tracking-[-0.2px] text-gray-500 dark:border-gray-800 dark:bg-white/3 dark:text-gray-400">
                  <span> ⌘ </span>
                  <span> K </span>
                </button>
              </div>
            </form>
          </div>
        </div>

        <div className="flex items-center gap-4 2xsm:gap-3">
          <nav aria-label={t.languages} className="flex gap-5 text-sm">
            <Link
              href="/pt/opac"
              hrefLang="pt-BR"
              aria-current={locale === "pt" ? "page" : undefined}
            >
              Português
            </Link>
            <Link
              href="/en/opac"
              hrefLang="en"
              aria-current={locale === "en" ? "page" : undefined}
            >
              English
            </Link>
          </nav>
          <div className="cursor-pointer">
            <ThemeToggleButton />
          </div>
          <UserArea locale={locale} />
        </div>
      </div>
    </header>
  );
}
