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

function initialThemeMode(): ThemeMode {
  if (typeof window === "undefined") return "light";

  try {
    const savedMode = localStorage.getItem("theme-mode");
    const legacyTheme = localStorage.getItem("theme");
    return isThemeMode(savedMode)
      ? savedMode
      : isThemeMode(legacyTheme)
        ? legacyTheme
        : "light";
  } catch {
    return "light";
  }
}

function initialSystemTheme(): ResolvedTheme {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [themeMode, setThemeMode] = useState<ThemeMode>(initialThemeMode);
  const [systemTheme, setSystemTheme] =
    useState<ResolvedTheme>(initialSystemTheme);
  const theme = themeMode === "auto" ? systemTheme : themeMode;

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const updateSystemTheme = (event: MediaQueryListEvent) =>
      setSystemTheme(event.matches ? "dark" : "light");
    mediaQuery.addEventListener("change", updateSystemTheme);
    return () => mediaQuery.removeEventListener("change", updateSystemTheme);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    document.documentElement.setAttribute("data-color-scheme", theme);
    try {
      localStorage.setItem("theme-mode", themeMode);
      localStorage.setItem("theme", theme);
    } catch {
      // Applying the theme does not depend on persisting the preference.
    }
  }, [theme, themeMode]);

  const toggleTheme = () => {
    setThemeMode((mode) =>
      (mode === "auto" ? systemTheme : mode) === "light" ? "dark" : "light",
    );
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
