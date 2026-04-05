import "@/styles/globals.css";
import "katex/dist/katex.min.css";

import { type Metadata } from "next";
import { Fira_Code, Fira_Sans } from "next/font/google";

import { ThemeProvider } from "@/components/theme-provider";
import { I18nProvider } from "@/core/i18n/context";
import { detectLocaleServer } from "@/core/i18n/server";

const firaSans = Fira_Sans({
  subsets: ["latin"],
  variable: "--font-fira-sans",
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const firaCode = Fira_Code({
  subsets: ["latin"],
  variable: "--font-fira-code",
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "VibeCFD",
    template: "%s - VibeCFD",
  },
  description:
    "VibeCFD is an industrial research workspace for simulation orchestration, evidence delivery, and skill-driven engineering workflows powered by DeerFlow and SkillNet ideas.",
};

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const locale = await detectLocaleServer();
  return (
    <html
      lang={locale}
      suppressContentEditableWarning
      suppressHydrationWarning
      className={`${firaSans.variable} ${firaCode.variable}`}
    >
      <body className="min-h-screen font-sans antialiased">
        <ThemeProvider
          attribute="class"
          forcedTheme="light"
          enableSystem={false}
          defaultTheme="light"
          disableTransitionOnChange
        >
          <I18nProvider initialLocale={locale}>{children}</I18nProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
