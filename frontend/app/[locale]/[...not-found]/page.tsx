import type { Metadata } from "next";
import Link from "next/link";
import { getCategoryRootsServer, type CategoryRecord } from "../../../lib/api/products";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../../lib/locale-url";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale: name } = await params;
  const locale = name === "en" ? "en" : "fa";
  return {
    title: locale === "en" ? "Page not found" : "صفحه پیدا نشد",
    robots: { index: false, follow: false },
    alternates: { canonical: absoluteUrl(localizedPath(locale, "/")), ...localizedAlternates("/") },
  };
}

export default async function LocaleNotFound({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: name } = await params;
  const locale = name === "en" ? "en" : "fa";
  const english = locale === "en";
  const categories = await getCategoryRootsServer<CategoryRecord[]>().catch(() => [] as CategoryRecord[]);
  const links = english ? [
    { href: `/${locale}`, label: "Home", primary: true },
    { href: `/${locale}/shop`, label: "All products", primary: false },
    { href: `/${locale}/categories`, label: "Categories", primary: false },
    { href: `/${locale}/rfq`, label: "Request a quote", primary: false },
    { href: `/${locale}/contact`, label: "Contact us", primary: false },
  ] : [
    { href: `/${locale}`, label: "صفحه اصلی", primary: true },
    { href: `/${locale}/shop`, label: "همه محصولات", primary: false },
    { href: `/${locale}/categories`, label: "دسته‌بندی‌ها", primary: false },
    { href: `/${locale}/rfq`, label: "درخواست پیش‌فاکتور", primary: false },
    { href: `/${locale}/contact`, label: "تماس با ما", primary: false },
  ];
  return <main className="site-container not-found-page">
    <div className="not-found-card">
      <span className="not-found-code" aria-hidden="true">404</span>
      <div className="section-kicker">{english ? "Error 404" : "خطای ۴۰۴"}</div>
      <h1>{english ? "This page is off the production line." : "این صفحه از خط تولید خارج شده است!"}</h1>
      <p>{english ? "The page you are looking for was moved, removed, or never existed. Try searching the catalog or start from one of the links below." : "صفحه‌ای که دنبال آن هستید منتقل شده، حذف شده یا اصلاً وجود نداشته است. در کاتالوگ جست‌وجو کنید یا از پیوندهای زیر شروع کنید."}</p>
      <form className="not-found-search" role="search" action={`/${locale}/search`} method="get">
        <input type="search" name="q" placeholder={english ? "Search products, brands, articles…" : "جست‌وجو در محصولات، برندها و دانش صنعتی…"} aria-label={english ? "Search the site" : "جست‌وجو در سایت"} />
        <button type="submit">{english ? "Search" : "جست‌وجو"}</button>
      </form>
      <nav className="not-found-links" aria-label={english ? "Helpful links" : "پیوندهای مفید"}>{links.map((link) => <Link key={link.href} href={link.href} className={link.primary ? "is-primary" : ""}>{link.label}</Link>)}</nav>
      {categories.length > 0 && <div className="not-found-cats"><span>{english ? "Or browse a category:" : "یا یک دسته را مرور کنید:"}</span><div>{categories.slice(0, 6).map((category) => <Link key={category.id} href={`/${locale}/category/${encodeURIComponent(category.slug)}`}>{category.name_fa}</Link>)}</div></div>}
    </div>
  </main>;
}
