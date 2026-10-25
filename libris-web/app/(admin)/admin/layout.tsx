// import { AppHeader } from "@/components/admin/AppHeader";
// import { AppSidebar } from "@/components/admin/AppSidebar";
import { Dasboard } from "@/components/admin/Dasboard";
// import UserArea from "@/components/user/UserArea";
import { IdentityArea } from "@/components/user/IdentityArea";
import { SidebarProvider } from "@/context/SidebarContext";
import { adminPermission, requireAdminPageAccess } from "../page-access";

export const instant = false;

export default async function AdminLayout({
  children,
}: LayoutProps<"/admin">) {
  const { identity } = await requireAdminPageAccess(
    { allOf: [adminPermission.systemAdmin] },
    "/admin",
  );

  return (
    <SidebarProvider>
      <Dasboard userArea={<IdentityArea identity={identity} />}>
        {children}
      </Dasboard>
    </SidebarProvider>
  );
}
