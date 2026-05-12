import type { Metadata } from "next";
import { Fraunces, Inter_Tight, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { TopNav } from "@/components/nav/TopNav";
import { QueryProvider } from "@/components/QueryProvider";

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-display-loaded",
  axes: ["opsz", "SOFT"],
  display: "swap",
});
const interTight = Inter_Tight({
  subsets: ["latin"],
  variable: "--font-ui-loaded",
  display: "swap",
});
const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono-loaded",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Vietnam Stock Filter — Terminal",
  description: "Editorial terminal for filtering and scoring Vietnamese equities.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${fraunces.variable} ${interTight.variable} ${jetbrains.variable}`}>
      <body
        style={{
          // Wire the next/font CSS variables into our @theme tokens.
          // (Tailwind v4's @theme tokens are CSS variables under the hood.)
          fontFamily: "var(--font-ui-loaded), system-ui, sans-serif",
        }}
      >
        <style>{`
          :root {
            --font-display: var(--font-display-loaded), "Times New Roman", serif;
            --font-ui: var(--font-ui-loaded), system-ui, sans-serif;
            --font-mono: var(--font-mono-loaded), ui-monospace, monospace;
          }
        `}</style>
        <QueryProvider>
          <div className="relative z-10 min-h-screen flex flex-col">
            <TopNav />
            <main className="flex-1">{children}</main>
          </div>
        </QueryProvider>
      </body>
    </html>
  );
}
