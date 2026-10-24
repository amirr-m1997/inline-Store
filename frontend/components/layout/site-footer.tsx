import Image from "next/image";
import Link from "next/link";
import { BackToTop } from "./back-to-top";
import { getFooterServer } from "../../lib/api/content";
import { getCatalogQueryServer } from "../../lib/api/products";

type FooterPayload = {
  company: {
    name_fa: string;
    logo: string | null;
    description: string;
    phone: string;
    mobile: string;
    email: string;
    address: string;
    website: string;
  } | null;
  sections: {
    id: number;
    title: string;
    links: { id: number; title: string; url: string; open_in_new_tab: boolean }[];
  }[];
  trust_badges: { id: number; title: string; image: string; url: string; alt: string }[];
  copyright: string;
};

type FooterLink = { label: string; href: string; external?: boolean; newTab?: boolean };

function toAsciiPhone(value: string): string {
  const faToEn: Record<string, string> = { "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4", "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9" };
  return value.replace(/[۰-۹]/g, (digit) => faToEn[digit] ?? digit).replace(/[^\d+]/g, "");
}

function FooterLinks({ links }: { links: FooterLink[] }) {
  return <ul className="footer-nav-list">{links.map((link) => <li key={link.href}>{link.external ? <a href={link.href} target={link.newTab ? "_blank" : undefined} rel={link.newTab ? "noreferrer" : undefined}>{link.label}<span aria-hidden="true" className="footer-link-arrow">←</span></a> : <Link href={link.href}>{link.label}<span aria-hidden="true" className="footer-link-arrow">←</span></Link>}</li>)}</ul>;
}

export async function SiteFooter({ locale = "fa" }: { locale?: string }) {
  const english = locale === "en";
  const [footer, discounts] = await Promise.all([
    getFooterServer<FooterPayload>().catch((error) => {
      console.error("Unable to load footer content.", error);
      return null;
    }),
    getCatalogQueryServer({ page_size: 1, discounted: "1" }).catch((error) => {
      console.error("Unable to check active discounted products for the footer.", error);
      return null;
    }),
  ]);

  const company = footer?.company;
  const companyName = company?.name_fa || (english ? "Mehr Asl Manufacturing Co." : "کارخانجات تولیدی مهراصل");
  const companyDesc = company?.description || (english
    ? "Mehr Asl Manufacturing was registered and established in 1990 with a focus on industrial air conditioning and refrigeration."
    : "شرکت تولیدی مهراصل در سال ۱۳۶۹ با زمینه فعالیت تهویه مطبوع و تبرید صنعتی ثبت و افتتاح شد.");
  const phone = company?.phone || "۰۲۱-۸۸۳۰۰۸۰۱";
  const factoryPhone = company?.mobile || "۰۴۱-۳۴۳۲۸۹۴۱";
  const email = company?.email || "sales.manager@mehrasl.ir";
  const address = company?.address || (english
    ? "Tehran: No. 17, Zohreh St., North Mofatteh Ave. | Tabriz Factory: Km 35 Azarshahr Road, Shahid Salimi Industrial Zone"
    : "دفتر مرکزی: تهران، خیابان مفتح شمالی، خیابان زهره، شماره ۱۷ | کارخانه مرکزی: تبریز، کیلومتر ۳۵ جاده آذرشهر، شهرک صنعتی شهید سلیمی");
  const copyright = english
    ? footer?.copyright || "All rights reserved for Mehr Asl Manufacturing Corporation. © 2026"
    : "تمام حقوق برای شرکت تولیدی مهر اصل محفوظ است.";
  const path = (value: string) => `/${locale}${value}`;
  const productLinks: FooterLink[] = [
    { label: english ? "All products" : "همه محصولات", href: path("/shop") },
    { label: english ? "Product categories" : "دسته‌بندی محصولات", href: path("/categories") },
    { label: english ? "Newest products" : "جدیدترین محصولات", href: path("/newest") },
    ...(discounts && discounts.total_count > 0 ? [{ label: english ? "Discounted products" : "محصولات تخفیف‌دار", href: path("/best-discounts") }] : []),
    { label: english ? "Search products and codes" : "جستجوی محصولات و کد فنی", href: path("/search") },
    { label: english ? "Technical articles" : "دانشنامه و راهنمای انتخاب", href: path("/knowledge") },
  ];
  const guideLinks: FooterLink[] = [
    { label: english ? "Frequently asked questions" : "سؤالات متداول", href: path("/faq") },
    { label: english ? "Track orders" : "پیگیری سفارش‌ها", href: path("/account/orders") },
    { label: english ? "Technical resources" : "منابع فنی", href: path("/support/resources") },
  ];
  const serviceLinks: FooterLink[] = [
    { label: english ? "Request a quotation" : "درخواست استعلام قیمت", href: path("/rfq") },
    { label: english ? "Contact sales" : "تماس با واحد فروش", href: path("/contact") },
    { label: english ? "Customer support" : "پشتیبانی مشتریان", href: path("/support") },
    { label: english ? "Submit a support request" : "ثبت درخواست پشتیبانی", href: path("/support/request") },
    { label: english ? "Warranty information" : "اطلاعات و درخواست گارانتی", href: path("/support/warranty") },
  ];
  const companyLinks: FooterLink[] = [
    { label: english ? "About Mehr Asl" : "درباره مهر اصل", href: path("/about") },
    ...(footer?.company?.website && /^https?:\/\//i.test(footer.company.website) ? [{ label: english ? "Company website" : "وب‌سایت شرکت", href: footer.company.website, external: true }] : []),
  ];
  const knownCompanyLinks = new Set(companyLinks.map((link) => link.href));
  for (const section of footer?.sections ?? []) {
    for (const link of section.links) {
      const validUrl = (link.url.startsWith("/") && !link.url.startsWith("//")) || /^https?:\/\//i.test(link.url);
      if (!validUrl || knownCompanyLinks.has(link.url)) continue;
      knownCompanyLinks.add(link.url);
      companyLinks.push({ label: link.title, href: link.url, external: /^https?:\/\//i.test(link.url), newTab: link.open_in_new_tab });
    }
  }

  return (
    <footer className="database-footer" aria-label={english ? "Site footer" : "پاورقی سایت"}>
      <div className="footer-main responsive-container">
        <section className="footer-col footer-company" aria-labelledby="footer-company-title">
          <div className="footer-brand">
            {company?.logo ? <Image src={company.logo} alt="" aria-hidden="true" width={92} height={92} sizes="68px" className="footer-logo-img" /> : <div className="footer-brand-mark" aria-hidden="true"><i>❄</i></div>}
            <div><h2 className="footer-company-name" id="footer-company-title">{companyName}</h2><span className="footer-brand-tagline">{english ? "Industrial HVAC & Refrigeration" : "تهویه مطبوع و تبرید صنعتی"}</span></div>
          </div>
          <p className="footer-description">{companyDesc}</p>
          <address className="footer-address-block">
            <div className="footer-contact-item"><span className="footer-contact-icon" aria-hidden="true">⌖</span><span className="footer-contact-text">{address}</span></div>
            <div className="footer-contact-item"><span className="footer-contact-icon" aria-hidden="true">☎</span><div><span className="footer-contact-label">{english ? "Sales:" : "دفتر فروش:"} </span><a href={`tel:${toAsciiPhone(phone)}`} dir="ltr" className="footer-contact-link">{phone}</a></div></div>
            {factoryPhone && <div className="footer-contact-item"><span className="footer-contact-icon" aria-hidden="true">☎</span><div><span className="footer-contact-label">{english ? "Factory:" : "کارخانه:"} </span><a href={`tel:${toAsciiPhone(factoryPhone)}`} dir="ltr" className="footer-contact-link">{factoryPhone}</a></div></div>}
            {email && <div className="footer-contact-item"><span className="footer-contact-icon" aria-hidden="true">✉</span><a href={`mailto:${email}`} dir="ltr" className="footer-contact-link">{email}</a></div>}
          </address>
        </section>

        <section className="footer-col" aria-labelledby="footer-products-title"><h2 className="footer-col-title" id="footer-products-title">{english ? "Products & search" : "خرید و محصولات"}</h2><nav aria-label={english ? "Products and search" : "محصولات و جستجو"}><FooterLinks links={productLinks} /></nav></section>
        <section className="footer-col" aria-labelledby="footer-guide-title"><h2 className="footer-col-title" id="footer-guide-title">{english ? "Buying guide" : "راهنمای خرید"}</h2><nav aria-label={english ? "Buying guide" : "راهنمای خرید"}><FooterLinks links={guideLinks} /></nav></section>
        <section className="footer-col" aria-labelledby="footer-service-title"><h2 className="footer-col-title" id="footer-service-title">{english ? "Customer service & business" : "خدمات مشتریان و فروش سازمانی"}</h2><nav aria-label={english ? "Customer and business services" : "خدمات مشتریان و فروش سازمانی"}><FooterLinks links={serviceLinks} /></nav></section>
        <section className="footer-col" aria-labelledby="footer-company-links-title"><h2 className="footer-col-title" id="footer-company-links-title">{english ? "Company information" : "درباره شرکت"}</h2><nav aria-label={english ? "Company information" : "درباره و اطلاعات شرکت"}><FooterLinks links={companyLinks} /></nav></section>
      </div>

      {footer?.trust_badges?.length ? <section className="footer-trust responsive-container" aria-labelledby="footer-trust-title">
        <h2 className="footer-trust-title" id="footer-trust-title">{english ? "Licenses & trust marks" : "مجوزها و نمادهای اعتماد"}</h2>
        <div className="footer-trust-badges">{footer.trust_badges.map((badge) => {
          const image = <Image src={badge.image} alt={badge.alt || badge.title} width={96} height={96} sizes="96px" />;
          const validUrl = /^https?:\/\//i.test(badge.url);
          return <div key={badge.id} className="footer-trust-item">{validUrl ? <a href={badge.url} target="_blank" rel="noreferrer" title={badge.title}>{image}</a> : image}</div>;
        })}</div>
      </section> : null}

      <div className="footer-bottom"><div className="responsive-container footer-bottom-inner">
        <p className="footer-copyright-text">{copyright}</p>
        <BackToTop english={english} />
      </div></div>
    </footer>
  );
}
