"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type ThemeMode = "light" | "dark" | "auto";
type ResolvedTheme = "light" | "dark";

type ThemeContextType = {
  theme: ResolvedTheme;
  themeMode: ThemeMode;
  setThemeMode: (mode: ThemeMode) => void;
  toggleTheme: () => void;
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

function isThemeMode(value: string | null): value is ThemeMode {
  return value === "light" || value === "dark" || value === "auto";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [themeMode, setThemeMode] = useState<ThemeMode>("light");
  const [systemTheme, setSystemTheme] = useState<ResolvedTheme>("light");
  const [isInitialized, setIsInitialized] = useState(false);
  const theme = themeMode === "auto" ? systemTheme : themeMode;

  useEffect(() => {
    try {
      const savedMode = localStorage.getItem("theme-mode");
      const legacyTheme = localStorage.getItem("theme");
      setThemeMode(isThemeMode(savedMode) ? savedMode : isThemeMode(legacyTheme) ? legacyTheme : "light");
    } catch {
      // The theme remains usable when browser storage is unavailable.
    }

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const updateSystemTheme = () => setSystemTheme(mediaQuery.matches ? "dark" : "light");
    updateSystemTheme();
    mediaQuery.addEventListener("change", updateSystemTheme);
    setIsInitialized(true);
    return () => mediaQuery.removeEventListener("change", updateSystemTheme);
  }, []);

  useEffect(() => {
    if (!isInitialized) return;

    document.documentElement.classList.toggle("dark", theme === "dark");
    document.documentElement.setAttribute("data-color-scheme", theme);
    try {
      localStorage.setItem("theme-mode", themeMode);
      localStorage.setItem("theme", theme);
    } catch {
      // Applying the theme does not depend on persisting the preference.
    }
  }, [theme, themeMode, isInitialized]);

  const toggleTheme = () => {
    setThemeMode((mode) => (mode === "auto" ? systemTheme : mode) === "light" ? "dark" : "light");
  };

  return (
    <ThemeContext.Provider value={{ theme, themeMode, setThemeMode, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
