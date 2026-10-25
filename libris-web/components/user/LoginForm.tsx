"use client";

import { usePathname, useSearchParams } from "next/navigation";

export function LoginForm() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const query = searchParams.toString();
  const returnTo = query ? `${pathname}?${query}` : pathname;

  return (
    <form action="/oidc/login" method="post">
      <input type="hidden" name="returnTo" value={returnTo} />
      <button
        type="submit"
        className="cursor-pointer rounded-lg border border-teal-800 bg-white px-5 py-2 font-semibold text-teal-900 transition-colors hover:bg-teal-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-700 dark:border-teal-300 dark:bg-gray-900 dark:text-teal-300 dark:hover:bg-gray-800 dark:focus-visible:outline-teal-300"
      >
        Login
      </button>
    </form>
  );
}
