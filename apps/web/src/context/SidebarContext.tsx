"use client";

import { createContext, useContext, useState } from "react";

type SidebarContextType = {
  isExpanded: boolean;
//   isMobileOpen: boolean;
//   isHovered: boolean;
//   activeItem: string | null;
//   openSubmenu: string | null;
//   toggleSidebar: () => void;
//   toggleMobileSidebar: () => void;
//   setIsHovered: (isHovered: boolean) => void;
//   setActiveItem: (item: string | null) => void;
//   toggleSubmenu: (item: string) => void;
};


const SidebarContext = createContext<SidebarContextType | undefined>(undefined);

export const useSidebar = () => {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider");
  }
  return context;
};

export const SidebarProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {

    const [isMobile, setIsMobile] = useState(false);
    const [isExpanded, setIsExpanded] = useState(true);
    
    return (
    <SidebarContext.Provider
      value={{
        isExpanded: isMobile ? false : isExpanded,
        // isMobileOpen,
        // isHovered,
        // activeItem,
        // openSubmenu,
        // toggleSidebar,
        // toggleMobileSidebar,
        // setIsHovered,
        // setActiveItem,
        // toggleSubmenu,
      }}
    >
      {children}
    </SidebarContext.Provider>
  );
}