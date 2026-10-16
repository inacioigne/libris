import { notFound, redirect } from "next/navigation";
import { isLocale } from "@/i18n/messages";

export default async function LocaleHome({ params, searchParams }: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(await searchParams)) {
    if (value === undefined) continue;
    for (const item of Array.isArray(value) ? value : [value]) query.append(key, item);
  }
  redirect(`/${locale}/opac${query.size ? `?${query}` : ""}`);
}
