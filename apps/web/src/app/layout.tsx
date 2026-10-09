import type { ReactNode } from "react";
// The locale layout owns <html> so each language has the correct document language.
export default function RootLayout({ children }: { children: ReactNode }) {
  return children;
}
