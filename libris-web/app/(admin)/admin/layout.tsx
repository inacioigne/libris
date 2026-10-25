import { AppHeader } from "@/components/admin/AppHeader";
import { AppSidebar } from "@/components/admin/AppSidebar";
import { Dasboard } from "@/components/admin/Dasboard";
import UserArea from "@/components/user/UserArea";
import { SidebarProvider } from "@/context/SidebarContext";


export default function Layout({ children }: LayoutProps<"/">) {
  return (
    <>
      <SidebarProvider>
        <Dasboard userArea={<UserArea />}>{children}</Dasboard>
      </SidebarProvider>
    </>
  );
}
