"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { getCategoryUrl } from "../../lib/category-url";
import type { NavCategory } from "./mega-menu";
import { CompanyAdvantages } from "./company-advantages";
import { ProductCard, type CatalogProduct } from "./product-card";
import { SiteHero } from "./site-hero";

type ProductResponse = { results?: CatalogProduct[] };
type SupplyBrand = { id: number; name: string; logo: string | null; website: string };

function ProductSection({ title, kicker, products, href, empty }: { title: string; kicker: string; products: CatalogProduct[]; href?: string; empty: string }) {
  return <section className="enterprise-section home-product-section site-container">
    <header className="home-section-heading"><div><div className="section-kicker">{kicker}</div><h2>{title}</h2></div>{href && <Link href={href}>مشاهده همه <span aria-hidden="true">←</span></Link>}</header>
    {products.length ? <div className="industrial-product-grid">{products.map((product) => <ProductCard key={product.id} product={product} />)}</div> : <div className="home-section-empty">{empty}</div>}
  </section>;
}

export function EnterpriseHome() {
  const { locale = "fa" } = useParams<{ locale: string }>();
  const [categories, setCategories] = useState<NavCategory[]>([]);
  const [featured, setFeatured] = useState<CatalogProduct[]>([]);
  const [newest, setNewest] = useState<CatalogProduct[]>([]);
  const [discounted, setDiscounted] = useState<CatalogProduct[]>([]);
  const [brands, setBrands] = useState<SupplyBrand[]>([]);

  useEffect(() => {
    const products = (url: string, setter: (items: CatalogProduct[]) => void) => fetch(url).then((response) => response.ok ? response.json() as Promise<ProductResponse> : { results: [] }).then((data) => setter(Array.isArray(data.results) ? data.results : [])).catch(() => setter([]));
    fetch("/api/v1/categories/roots/").then((response) => response.ok ? response.json() as Promise<NavCategory[]> : []).then((data) => setCategories(Array.isArray(data) ? data : [])).catch(() => setCategories([]));
    products("/api/v1/products/?featured=true&page_size=8", setFeatured);
    products("/api/v1/products/?ordering=-created_at&page_size=8", setNewest);
    products("/api/v1/products/?discounted=true&ordering=-discount_percentage&page_size=8", setDiscounted);
    fetch("/api/v1/supply-brands/").then((response) => response.ok ? response.json() as Promise<SupplyBrand[]> : []).then((data) => setBrands(Array.isArray(data) ? data : [])).catch(() => setBrands([]));
  }, []);

  return <main className="enterprise-home">
    <SiteHero />
    <CompanyAdvantages />
    <section id="categories" className="enterprise-section site-container"><div className="section-kicker">دسترسی سریع</div><h2>دسته‌بندی‌های اصلی</h2><div className="root-cards">{categories.map((category) => <Link key={category.id} href={getCategoryUrl(category, locale)}><span>دسته اصلی</span><b>{category.name_fa}</b><i>مشاهده زیرگروه‌ها ←</i></Link>)}</div></section>
    <ProductSection title="محصولات منتخب" kicker="انتخاب مدیریت فروشگاه" products={featured} href={`/${locale}/shop`} empty="هنوز محصولی به‌عنوان منتخب تعیین نشده است." />
    <ProductSection title="جدیدترین محصولات" kicker="تازه‌های کاتالوگ" products={newest} href={`/${locale}/newest`} empty="محصول جدیدی ثبت نشده است." />
    <ProductSection title="بیشترین تخفیف‌ها" kicker="فرصت‌های خرید" products={discounted} href={`/${locale}/best-discounts`} empty="در حال حاضر محصول تخفیف‌داری وجود ندارد." />
    <section className="enterprise-section supply-brands-section site-container"><div className="section-kicker">شبکه تأمین</div><h2>برندهای قابل تأمین</h2>{brands.length ? <div className="supply-brand-grid">{brands.map((brand) => { const content = <>{brand.logo ? <Image src={brand.logo} alt={`لوگوی ${brand.name}`} width={120} height={64} /> : <span aria-hidden="true">{brand.name.slice(0, 1)}</span>}<b>{brand.name}</b></>; return brand.website ? <a key={brand.id} href={brand.website} target="_blank" rel="noreferrer">{content}</a> : <article key={brand.id}>{content}</article>; })}</div> : <div className="home-section-empty">فهرست برندهای قابل تأمین به‌زودی تکمیل می‌شود.</div>}</section>
    <section className="home-quote-cta site-container"><div><span>خرید سازمانی و صنعتی</span><h2>برای استعلام موجودی و قیمت روز آماده‌ایم</h2><p>مشخصات فنی یا کد کالای مورد نیازتان را ارسال کنید تا کارشناسان فروش پاسخ دهند.</p></div><div><Link className="primary" href={`/${locale}/contact`}>درخواست استعلام</Link><Link href={`/${locale}/shop`}>مشاهده محصولات</Link></div></section>
  </main>;
}
