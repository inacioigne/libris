import { defineRouting } from "next-intl/routing";

export const routing = defineRouting({
  locales: ["pt"], // expand when multilang is needed
  defaultLocale: "pt",
  localePrefix: "never",
});

export type Locale = (typeof routing.locales)[number];
