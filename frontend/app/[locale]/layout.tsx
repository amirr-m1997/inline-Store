import "../globals.css";
import { notFound } from "next/navigation";
import Script from "next/script";
import type { ReactNode } from "react";
import { getLocaleConfig, isLocale } from "../../lib/i18n";
import { ThemeToggle } from "../../components/layout/theme-toggle";
import { SiteHeader } from "../../components/layout/site-header";
import { SiteFooter } from "../../components/layout/site-footer";
import { getCompanyServer } from "../../lib/api/content";
import type { CompanyInfo } from "../../types/api";
export function generateStaticParams() { return [{ locale: "fa" }, { locale: "en" }]; }
export default async function LocaleLayout({ children, params }: { children: ReactNode; params: Promise<{ locale: string }> }) {
  const { locale: localeName } = await params;
  if (!isLocale(localeName)) notFound();
  const locale = getLocaleConfig(localeName);
  const company = await getCompanyServer<CompanyInfo>().catch(() => null);
  return <html lang={locale.lang} dir={locale.dir} suppressHydrationWarning><body><Script id="theme-init" strategy="beforeInteractive">{`(() => { try { const saved = localStorage.getItem("theme"); const dark = saved ? saved === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches; document.documentElement.classList.toggle("dark", dark); } catch (_) {} })();`}</Script><SiteHeader initialCompany={company} />{children}<SiteFooter locale={localeName} /></body></html>;
}
