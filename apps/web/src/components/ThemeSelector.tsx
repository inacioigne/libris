"use client";

import { useTheme } from "../context/ThemeContext";
import { messages, type Locale } from "../i18n/messages";

export function ThemeSelector({ locale }: { locale: Locale }) {
  const { themeMode, setThemeMode } = useTheme();
  const t = messages[locale];

  return (
    <label className="flex items-center gap-2 text-sm">
      {t.themeLabel}
      <select
        value={themeMode}
        onChange={(event) => {
          const mode = event.target.value;
          if (mode === "light" || mode === "dark" || mode === "auto") setThemeMode(mode);
        }}
        className="rounded-lg border border-slate-200 bg-white px-3 py-2 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
      >
        <option value="light">{t.themeLight}</option>
        <option value="dark">{t.themeDark}</option>
        <option value="auto">{t.themeAuto}</option>
      </select>
    </label>
  );
}
