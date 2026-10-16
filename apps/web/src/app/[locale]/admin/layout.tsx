import type { ReactNode } from "react";
import { Dasboard } from "@/layout/Dasboard";
import { isLocale } from "@/i18n/messages";
import { notFound } from "next/navigation";
import UserArea from "@/components/header/UserArea";

export default async function OpacLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return (
    <Dasboard 
    locale={locale} 
    userArea={<UserArea locale={locale} />}>
      {children}
    </Dasboard>
  );
}
