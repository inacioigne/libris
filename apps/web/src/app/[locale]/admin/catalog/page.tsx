import { redirect } from "next/navigation";
import { isLocale } from "@/i18n/messages";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export default async function AdminCatalogIndex({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!isLocale(locale)) {
    redirect("/pt/admin");
  }
  redirect(`/${locale}/admin/catalog/works`);
}
