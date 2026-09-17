import "@fontsource/vazirmatn/400.css";
import "@fontsource/vazirmatn/700.css";
import "@fontsource/vazirmatn/900.css";
import "../globals.css";
import "../storefront-refresh.css";
import { notFound } from "next/navigation";
import Script from "next/script";
import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { getLocaleConfig, isLocale } from "../../lib/i18n";
import { absoluteUrl } from "../../lib/locale-url";
import { SiteHeader } from "../../components/layout/site-header";
import { SiteFooter } from "../../components/layout/site-footer";
import { ProductCompareTray } from "../../components/catalog/product-compare-tray";
import { getCompanyServer } from "../../lib/api/content";
import type { CompanyInfo } from "../../types/api";
export function generateStaticParams() { return [{ locale: "fa" }, { locale: "en" }]; }
export const viewport: Viewport = { width: "device-width", initialScale: 1 };
export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale: localeName } = await params;
  const locale = isLocale(localeName) ? localeName : "fa";
  return {
    metadataBase: new URL(absoluteUrl("/")),
    title: { default: locale === "en" ? "Company Store" : "فروشگاه شرکت", template: "%s" },
    alternates: { canonical: absoluteUrl(`/${locale}`), languages: { fa: absoluteUrl("/fa"), en: absoluteUrl("/en") } },
  };
}
export default async function LocaleLayout({ children, params }: { children: ReactNode; params: Promise<{ locale: string }> }) {
  const { locale: localeName } = await params;
  if (!isLocale(localeName)) notFound();
  const locale = getLocaleConfig(localeName);
  const company = await getCompanyServer<CompanyInfo>().catch(() => null);
  return <html lang={locale.lang} dir={locale.dir} suppressHydrationWarning><body><Script id="theme-init" strategy="beforeInteractive">{`(() => { try { const saved = localStorage.getItem("theme"); const dark = saved === "dark"; document.documentElement.classList.toggle("dark", dark); } catch (_) {} })();`}</Script><SiteHeader initialCompany={company} />{children}<ProductCompareTray locale={localeName} /><SiteFooter locale={localeName} /></body></html>;
}
