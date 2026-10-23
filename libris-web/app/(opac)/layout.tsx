import type { Metadata } from "next";
import "../globals.css";
import Header from "@/components/opac/header";

export const metadata: Metadata = {
  title: "Libris App",
  description: "Libris App",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
       className={`h-full antialiased`}
    >
      <body 
      // className="min-h-full flex flex-col"
      >
        <Header />
        {children}</body>
    </html>
  );
}
