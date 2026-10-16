// "use client";
import type { ReactNode } from "react";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/messages";
import { AppHeader } from "@/layout/admin/AppHeader";
import { AppSidebar } from "@/layout/admin/AppSidebar";
import { useSidebar } from "@/context/SidebarContext";
import { Dasboard } from "@/layout/Dasboard";

export default function OpacLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ locale: string }>;
}) {
  // const { locale } = await params;
  // const { isExpanded, isHovered, isMobileOpen } = useSidebar();
  // const mainContentMargin = isMobileOpen
  //   ? "ml-0"
  //   : isExpanded || isHovered
  //     ? "lg:ml-[290px]"
  //     : "lg:ml-[90px]";
  // if (!isLocale(locale)) notFound();
  return (
    <Dasboard locale={"pt"} >
      {children}
    </Dasboard>
  );
}
