// "use client";
import { SidebarProvider } from "@/context/SidebarContext";


export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
 

  

  return (
    <SidebarProvider>
    
      {children}
    

    </SidebarProvider>
    
  );
}
