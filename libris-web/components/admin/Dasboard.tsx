"use client";
import { useSidebar } from "@/context/SidebarContext";
import { ReactNode } from "react";
import { AppSidebar } from "./AppSidebar";
import { AppHeader } from "./AppHeader";

type DashboardProps = {
  children: ReactNode;
  userArea: ReactNode;
};

export function Dasboard(
  {
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
      <AppSidebar  />
      <div
        className={`flex-1 transition-all  duration-300 ease-in-out ${mainContentMargin}`}
      >
        <AppHeader userArea={userArea} />
        {children}
      </div>
    </div>
  );
}
