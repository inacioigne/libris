import type { ReactNode } from "react";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/messages";
import AppHeader from "@/layout/opac/AppHeader";

export default async function OpacLayout({ children, params }: {
  children: ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return <><AppHeader locale={locale} />{children}</>;
}
