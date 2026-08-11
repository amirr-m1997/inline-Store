import "../globals.css";
import { notFound } from "next/navigation";
import type { ReactNode } from "react";
import { getLocaleConfig, isLocale } from "../../lib/i18n";
import { ThemeToggle } from "../../components/layout/theme-toggle";
import { SiteHeader } from "../../components/layout/site-header";
import { SiteFooter } from "../../components/layout/site-footer";
export function generateStaticParams() { return [{ locale: "fa" }, { locale: "en" }]; }
export default async function LocaleLayout({ children, params }: { children: ReactNode; params: Promise<{ locale: string }> }) {
  const { locale: localeName } = await params;
  if (!isLocale(localeName)) notFound();
  const locale = getLocaleConfig(localeName);
  return <html lang={locale.lang} dir={locale.dir}><body><SiteHeader />{children}<SiteFooter /></body></html>;
}
