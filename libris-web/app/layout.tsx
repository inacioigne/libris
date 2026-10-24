import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/opac/header";
import { ThemeProvider } from "../context/ThemeContext";

export const metadata: Metadata = {
  title: "Libris App",
  description: "Libris App",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="pt" className={`h-full antialiased`}>
      <body className="bg-white text-teal-900 transition-colors dark:bg-gray-900 dark:text-gray-100">
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
