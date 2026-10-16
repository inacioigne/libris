"use client";
import { useSidebar } from "@/context/SidebarContext";
import { AppSidebar } from "./admin/AppSidebar";
import { AppHeader } from "./admin/AppHeader";
import { Locale } from "@/i18n/messages";
import { ReactNode } from "react";

type DashboardProps = {
  locale: Locale;
  children: ReactNode;
  userArea: ReactNode;
};

export function Dasboard(
  {
  locale,
  children,
  userArea,
}: DashboardProps
) {
  const { isExpanded, isHovered, isMobileOpen } = useSidebar();
  const mainContentMargin = isMobileOpen
    ? "ml-0"
    : isExpanded || isHovered
      ? "lg:ml-[290px]"
      : "lg:ml-[90px]";

  return (
    <div className="min-h-screen xl:flex">
      <AppSidebar locale={locale} />
      <div
        className={`flex-1 transition-all  duration-300 ease-in-out ${mainContentMargin}`}
      >
        <AppHeader locale={locale} userArea={userArea} />
        {children}
      </div>
    </div>
  );
}
