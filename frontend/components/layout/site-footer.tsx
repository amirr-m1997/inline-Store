import Image from "next/image";
import Link from "next/link";
import { getCapabilitiesServer, getFooterServer, getIndustriesServer } from "../../lib/api/content";

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

const isInternal = (url: string) => url.startsWith("/");

function toAsciiPhone(val: string): string {
  const faToEn: Record<string, string> = {
    "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4",
    "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
  };
  const normalized = val.replace(/[۰-۹]/g, (d) => faToEn[d] ?? d);
  return normalized.replace(/[^\d+]/g, "");
}

export async function SiteFooter({ locale = "fa" }: { locale?: string }) {
  const english = locale === "en";

  const [footer, capabilities, industries] = await Promise.all([
    getFooterServer<FooterPayload>().catch(() => null),
    getCapabilitiesServer<{ id: number; slug: string; title_fa: string }[]>().catch(() => []),
    getIndustriesServer<{ id: number; slug: string; name_fa: string }[]>().catch(() => []),
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
  const copyright = footer?.copyright || (english
    ? "All rights reserved for Mehr Asl Manufacturing Corporation. © 2026"
    : "کلیه حقوق مادی و معنوی متعلق به شرکت کارخانجات تولیدی مهراصل می‌باشد. © ۱۴۰۴ - ۲۰۲۶");

  const quickLinks = [
    { label: english ? "Home" : "صفحه اصلی", href: `/${locale}` },
    { label: english ? "Product Catalog" : "کاتالوگ محصولات", href: `/${locale}/shop` },
    { label: english ? "Categories" : "دسته‌بندی‌ها", href: `/${locale}/categories` },
    { label: english ? "About MehrAsl" : "درباره مهراصل", href: `/${locale}/about` },
    { label: english ? "Contact Us" : "تماس با ما", href: `/${locale}/contact` },
  ];

  const customerServices = [
    { label: english ? "Request a Quote (RFQ)" : "درخواست استعلام قیمت (RFQ)", href: `/${locale}/rfq` },
    { label: english ? "Technical Support" : "پشتیبانی و خدمات پس از فروش", href: `/${locale}/support` },
    { label: english ? "Warranty Conditions" : "شرایط و ضوابط گارانتی", href: `/${locale}/support/warranty` },
    { label: english ? "Frequently Asked Questions" : "سوالات متداول (FAQ)", href: `/${locale}/faq` },
    { label: english ? "Technical Knowledge & Articles" : "دانشنامه و مقالات فنی", href: `/${locale}/knowledge` },
  ];

  const keyCategories = [
    { label: english ? "Industrial Chillers" : "چیلرهای صنعتی", href: `/${locale}/shop?q=${encodeURIComponent("چیلر")}` },
    { label: english ? "Air Handlers & Units" : "پکیج یونیت و هواساز", href: `/${locale}/shop?q=${encodeURIComponent("هواساز")}` },
    { label: english ? "Cooling Towers" : "برج‌های خنک‌کننده", href: `/${locale}/shop?q=${encodeURIComponent("برج")}` },
    { label: english ? "Industries & Applications" : "صنایع و کاربردها", href: `/${locale}/industries` },
    { label: english ? "Manufacturing Capabilities" : "توانمندی‌های تولیدی", href: `/${locale}/capabilities` },
  ];

  return (
    <footer className="database-footer" role="contentinfo" aria-label={english ? "Site footer" : "پاورقی سایت"}>
      <div className="footer-main responsive-container">
        {/* Column 1: Company / Brand + Quick Access */}
        <section className="footer-col footer-company" aria-label={companyName}>
          <div className="footer-brand">
            {company?.logo ? (
              <Image src={company.logo} alt={companyName} width={92} height={92} sizes="92px" className="footer-logo-img" />
            ) : (
              <div className="footer-brand-mark" aria-hidden="true">
                <i>❄</i>
              </div>
            )}
            <div>
              <h2 className="footer-company-name">{companyName}</h2>
              <span className="footer-brand-tagline">
                {english ? "Established 1990 • Industrial HVAC & Refrigeration" : "تأسیس ۱۳۶۹ • تهویه مطبوع و تبرید صنعتی"}
              </span>
            </div>
          </div>
          <p className="footer-description">{companyDesc}</p>

          {/* Quick Access merged into company column */}
          <div style={{ marginTop: 'var(--space-6)' }}>
            <h2 className="footer-col-title">{english ? "Quick Access" : "دسترسی سریع"}</h2>
            <ul className="footer-nav-list">
              {quickLinks.map((link, idx) => (
                <li key={idx}>
                  <Link href={link.href}>
                    <span>{link.label}</span>
                    <span aria-hidden="true" className="footer-link-arrow rtl:rotate-180 inline-block">←</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Column 2: Customer Services + Products & Industries */}
        <section className="footer-col" aria-label={english ? "Services & Products" : "خدمات و محصولات"}>
          <h2 className="footer-col-title">{english ? "Services & Products" : "خدمات و محصولات"}</h2>
          <ul className="footer-nav-list">
            {customerServices.map((service, idx) => (
              <li key={idx}>
                <Link href={service.href}>
                  <span>{service.label}</span>
                  <span aria-hidden="true" className="footer-link-arrow rtl:rotate-180 inline-block">←</span>
                </Link>
              </li>
            ))}
            {footer?.sections && footer.sections.length > 0 ? (
              footer.sections.flatMap((s) => s.links).slice(0, 4).map((link) => (
                <li key={link.id}>
                  {isInternal(link.url) && !link.open_in_new_tab ? (
                    <Link href={link.url}>
                      <span>{link.title}</span>
                      <span aria-hidden="true" className="footer-link-arrow rtl:rotate-180 inline-block">←</span>
                    </Link>
                  ) : (
                    <a href={link.url} target={link.open_in_new_tab ? "_blank" : undefined} rel={link.open_in_new_tab ? "noreferrer" : undefined}>
                      <span>{link.title}</span>
                      <span aria-hidden="true" className="footer-link-arrow rtl:rotate-180 inline-block">←</span>
                    </a>
                  )}
                </li>
              ))
            ) : (
              keyCategories.map((item, idx) => (
                <li key={idx}>
                  <Link href={item.href}>
                    <span>{item.label}</span>
                    <span aria-hidden="true" className="footer-link-arrow rtl:rotate-180 inline-block">←</span>
                  </Link>
                </li>
              ))
            )}
            {industries.length > 0 && !footer?.sections?.length && (
              <li>
                <Link href={`/${locale}/industries`}>
                  <span>{english ? "Industries & Applications" : "صنایع و کاربردها"}</span>
                  <span aria-hidden="true" className="footer-link-arrow rtl:rotate-180 inline-block">←</span>
                </Link>
              </li>
            )}
            {capabilities.length > 0 && !footer?.sections?.length && (
              <li>
                <Link href={`/${locale}/capabilities`}>
                  <span>{english ? "Company Capabilities" : "توانمندی‌های شرکت"}</span>
                  <span aria-hidden="true" className="footer-link-arrow rtl:rotate-180 inline-block">←</span>
                </Link>
              </li>
            )}
          </ul>
        </section>

        {/* Column 3: Contact Information (wider) */}
        <section className="footer-col footer-contact" style={{ gridColumn: 'span 1', minWidth: '280px' }} aria-label={english ? "Contact Information" : "اطلاعات تماس"}>
          <h2 className="footer-col-title">{english ? "Contact Us" : "اطلاعات تماس"}</h2>
          <address className="footer-address-block">
            <div className="footer-contact-item">
              <span className="footer-contact-icon" aria-hidden="true">📍</span>
              <span className="footer-contact-text">{address}</span>
            </div>
            <div className="footer-contact-item">
              <span className="footer-contact-icon" aria-hidden="true">☎</span>
              <div>
                <span className="footer-contact-label">{english ? "Sales Office:" : "دفتر فروش:"} </span>
                <a href={`tel:${toAsciiPhone(phone)}`} dir="ltr" className="footer-contact-link">
                  {phone}
                </a>
              </div>
            </div>
            <div className="footer-contact-item">
              <span className="footer-contact-icon" aria-hidden="true">🏭</span>
              <div>
                <span className="footer-contact-label">{english ? "Central Plant:" : "کارخانجات:"} </span>
                <a href={`tel:${toAsciiPhone(factoryPhone)}`} dir="ltr" className="footer-contact-link">
                  {factoryPhone}
                </a>
              </div>
            </div>
            <div className="footer-contact-item">
              <span className="footer-contact-icon" aria-hidden="true">✉</span>
              <a href={`mailto:${email}`} dir="ltr" className="footer-contact-link">
                {email}
              </a>
            </div>
          </address>
        </section>
      </div>

      {/* Trust Badges */}
      {footer?.trust_badges && footer.trust_badges.length > 0 && (
        <section className="footer-trust responsive-container" aria-label={english ? "Trust certificates" : "نشان‌های اعتماد"}>
          {footer.trust_badges.map((badge) => {
            const image = <Image src={badge.image} alt={badge.alt} width={96} height={96} sizes="96px" />;
            return (
              <div key={badge.id} className="footer-trust-item">
                {badge.url ? (
                  <a href={badge.url} target="_blank" rel="noreferrer" title={badge.title}>
                    {image}
                  </a>
                ) : (
                  image
                )}
              </div>
            );
          })}
        </section>
      )}

      {/* Bottom Bar */}
      <div className="footer-bottom">
        <div className="responsive-container footer-bottom-inner">
          <p className="footer-copyright-text">{copyright}</p>
          <nav className="footer-bottom-nav" aria-label={english ? "Legal links" : "پیوندهای حقوقی"}>
            <Link href={`/${locale}/about`}>{english ? "About" : "درباره ما"}</Link>
            <span className="footer-bottom-divider" aria-hidden="true">•</span>
            <Link href={`/${locale}/contact`}>{english ? "Contact" : "تماس"}</Link>
            <span className="footer-bottom-divider" aria-hidden="true">•</span>
            <Link href={`/${locale}/faq`}>{english ? "FAQ" : "سوالات متداول"}</Link>
            <span className="footer-bottom-divider" aria-hidden="true">•</span>
            <Link href={`/${locale}/support/warranty`}>{english ? "Warranty" : "گارانتی"}</Link>
          </nav>
        </div>
      </div>
    </footer>
  );
}
