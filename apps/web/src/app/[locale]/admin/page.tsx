import type { ReactNode } from "react";
import { notFound } from "next/navigation";
import { isLocale, messages } from "@/i18n/messages";
import { requestIdentity } from "@/server/auth/request";
import { guardAdminContent } from "@/server/admin/access";
import { AdminAccessState, AdminFrame, AdminShell } from "@/server/admin/shell";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export default async function AdminPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const query = await searchParams;
  const feedback =
    query.auth === "cancelled"
      ? messages[locale].cancelled
      : query.auth === "error"
        ? messages[locale].authError
        : undefined;

  const content = await guardAdminContent<ReactNode>(
    requestIdentity,
    (access) => <AdminShell locale={locale} access={access} />,
    (access) => (
      <AdminAccessState locale={locale} access={access} feedback={feedback} />
    ),
  );

//   if (content.status === "login_required" || content.status === "session_expired") {
    
//   }

//  console.log("[Login..]", content)
  

  // return <AdminFrame locale={locale}>
  //   {content}
  //   {/* {JSON.stringify(content)} */}
  //   </AdminFrame>;
  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <h1>Libris</h1>
       

    </main>
  )
}
