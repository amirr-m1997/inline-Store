import Image from "next/image";
import Link from "next/link";
import { FiPhone, FiMail, FiMapPin, FiChevronLeft } from "react-icons/fi";
import { FaWhatsapp, FaTelegramPlane, FaLinkedinIn, FaInstagram } from "react-icons/fa";
import { getFooterServer } from "../../lib/api/content";
import { FooterAccordionCol } from "./footer-accordion-col";

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

type FooterLink = { id?: string | number; label: string; href: string; external?: boolean; newTab?: boolean };

function normalizeLegacyFooterUrl(url: string, locale: string) {
  const normalized = url.trim();
  if (/^\/?fa\/category\/search\?ordering=-created_at$/i.test(normalized) || /^\/?category\/search\?ordering=-created_at$/i.test(normalized)) return `/${locale}/newest`;
  if (/^\/?fa\/category\/search\?discount=true$/i.test(normalized) || /^\/?category\/search\?discount=true$/i.test(normalized)) return `/${locale}/best-discounts`;
  return normalized;
}

function toAsciiPhone(value: string): string {
  const faToEn: Record<string, string> = { "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4", "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9" };
  return value.replace(/[۰-۹]/g, (digit) => faToEn[digit] ?? digit).replace(/[^\d+]/g, "");
}

function displayPhone(value: string): string {
  return value.trim().replace(/^[^\d۰-۹+]+/, "");
}

function FooterLinks({ links }: { links: FooterLink[] }) {
  return (
    <ul className="footer-nav-list">
      {links.map((link, index) => {
        const key = link.id ? `link-${link.id}` : `link-${link.href}-${index}`;
        return (
          <li key={key}>
            {link.external ? (
              <a href={link.href} target={link.newTab ? "_blank" : undefined} rel={link.newTab ? "noreferrer" : undefined}>
                <FiChevronLeft size={13} className="footer-link-icon" aria-hidden="true" />
                <span>{link.label}</span>
              </a>
            ) : (
              <Link href={link.href}>
                <FiChevronLeft size={13} className="footer-link-icon" aria-hidden="true" />
                <span>{link.label}</span>
              </Link>
            )}
          </li>
        );
      })}
    </ul>
  );
}

export async function SiteFooter({ locale = "fa" }: { locale?: string }) {
  const english = locale === "en";
  const footer = await getFooterServer<FooterPayload>().catch((error) => {
    console.error("Unable to load footer content.", error);
    return null;
  });

  const company = footer?.company;
  const companyName = company?.name_fa || (english ? "Mehr Asl Manufacturing Co." : "شرکت تولیدی مهر اصل");
  const companyDesc =
    company?.description ||
    (english
      ? "Manufacturer and specialist supplier of industrial refrigeration, HVAC equipment, and chillers nationwide."
      : "تولیدکننده و تأمین‌کننده تجهیزات تهویه مطبوع، چیلرها و برودت صنعتی با ضمانت اصالت کالا و خدمات پس از فروش سراسری.");
  const phone = company?.phone || "۰۲۱-۶۷۳۸۹۸۸۵";
  const factoryPhone = company?.mobile || "۰۴۱-۳۳۳۸۹۸۸۵";
  const email = company?.email || "sales.manager@mehrasl.ir";
  const address =
    company?.address ||
    (english
      ? "Tehran Central Office: Ayatollah Hashemi Rafsanjani Expy, Shahid Sattari St. | Tabriz Factory: Km 35 Azarshahr Rd, Shahid Salimi Zone"
      : "تهران: بزرگراه آیت‌الله هاشمی رفسنجانی، خیابان شهید ستاری | کارخانه: تبریز، کیلومتر ۳۵ جاده آذرشهر، شهرک صنعتی شهید سلیمی");
  const copyright = english
    ? footer?.copyright || "All rights reserved for Mehr Asl Manufacturing Corporation. © 2026"
    : "تمامی حقوق برای شرکت تولیدی مهر اصل محفوظ است.";

  const path = (value: string) => `/${locale}${value}`;

  // Structured columns matching standard prompt with exactly 5 to 6 links per column
  const productLinks: FooterLink[] = [
    { id: "all-products", label: english ? "All products" : "همه محصولات", href: path("/shop") },
    { id: "categories", label: english ? "Product categories" : "دسته‌بندی‌های اصلی", href: path("/categories") },
    { id: "brands", label: english ? "Industrial brands" : "برندهای معتبر صنعتی", href: path("/shop") },
    { id: "advanced-search", label: english ? "Advanced search" : "جستجوی پیشرفته و کد فنی", href: path("/search") },
    { id: "discounts", label: english ? "Discounted products" : "محصولات تخفیف‌دار", href: path("/best-discounts") },
    { id: "newest", label: english ? "Newest products" : "جدیدترین محصولات", href: path("/newest") },
  ];

  const serviceLinks: FooterLink[] = [
    { id: "project-orders", label: english ? "Project orders" : "ثبت سفارشات پروژه‌ای", href: path("/rfq") },
    { id: "quote", label: english ? "Request quotation" : "درخواست پیش‌فاکتور رسمی", href: path("/rfq") },
    { id: "track-order", label: english ? "Track orders" : "پیگیری سفارش‌ها", href: path("/account/orders") },
    { id: "support", label: english ? "Customer support" : "پشتیبانی و امور مشتریان", href: path("/support") },
    { id: "sales-contact", label: english ? "Contact sales" : "تماس مستقیم با واحد فروش", href: path("/contact") },
    { id: "warranty", label: english ? "Warranty services" : "اطلاعات و خدمات گارانتی", href: path("/support/warranty") },
  ];

  const companyLinks: FooterLink[] = [
    { id: "about", label: english ? "About company" : "درباره شرکت", href: path("/about") },
    { id: "factory", label: english ? "Factory specs" : "مشخصات و خطوط کارخانه", href: path("/about") },
    { id: "knowledge", label: english ? "Articles & news" : "آخرین مقالات و اخبار فنی", href: path("/knowledge") },
    { id: "faq", label: english ? "FAQ" : "سؤالات متداول", href: path("/faq") },
    { id: "contact", label: english ? "Contact us" : "تماس مستقیم با ما", href: path("/contact") },
    ...(company?.website && /^https?:\/\//i.test(company.website)
      ? [{ id: "website", label: english ? "Company website" : "وب‌سایت رسمی شرکت", href: company.website, external: true }]
      : [{ id: "terms", label: english ? "Terms of service" : "شرایط و قوانین فروش", href: path("/faq") }]),
  ];

  // Dynamically attach any custom database links created in Django admin that aren't already represented
  const existingHrefs = new Set([
    ...productLinks.map((l) => l.href),
    ...serviceLinks.map((l) => l.href),
    ...companyLinks.map((l) => l.href),
    path("/account"),
    path("/cart"),
  ]);

  for (const section of footer?.sections ?? []) {
    const sTitle = section.title.toLowerCase();
    for (const link of section.links) {
      const url = normalizeLegacyFooterUrl(link.url, locale);
      const validUrl = (url.startsWith("/") && !url.startsWith("//")) || /^https?:\/\//i.test(url);
      if (!validUrl || existingHrefs.has(url)) continue;
      existingHrefs.add(url);

      const footerItem: FooterLink = {
        id: `db-${link.id}`,
        label: link.title,
        href: url,
        external: /^https?:\/\//i.test(url),
        newTab: link.open_in_new_tab,
      };

      if (sTitle.includes("فروشگاه") || sTitle.includes("محصول") || url.includes("/shop") || url.includes("/categor")) {
        productLinks.push(footerItem);
      } else if (sTitle.includes("پشتیبانی") || url.includes("/support")) {
        serviceLinks.push(footerItem);
      } else {
        companyLinks.push(footerItem);
      }
    }
  }

  const badges = footer?.trust_badges?.length
    ? footer.trust_badges
    : [
        { id: 1, title: "نماد اعتماد الکترونیکی (eNamad)", image: "", url: "#", alt: "نماد اعتماد الکترونیکی" },
        { id: 2, title: "گواهینامه‌های استاندارد و ایزو صنعتی", image: "", url: "#", alt: "استاندارد ملی و ایزو" },
      ];

  return (
    <footer className="database-footer" aria-label={english ? "Site footer" : "پاورقی سایت"}>
      <div className="responsive-container">
        {/* 5-Column Grid */}
        <div className="footer-main">
          {/* Column 1: Company & Live Contact Info */}
          <section className="footer-col footer-company" aria-labelledby="footer-company-title">
            <div className="ma-brand-header">
              <Link href={`/${locale}`} className="ma-footer-logo-link" aria-label={`صفحه اصلی ${companyName}`}>
                {company?.logo ? (
                  <Image src={company.logo} alt="" aria-hidden="true" width={220} height={90} sizes="(max-width: 768px) 180px, 220px" className="ma-footer-logo-img" />
                ) : (
                  <h2 id="footer-company-title" className="ma-brand-fallback-title">{companyName}</h2>
                )}
              </Link>
            </div>
            <p className="ma-brand-desc">{companyDesc}</p>
            <div className="ma-contact-list">
              <div className="ma-contact-item">
                <span className="ma-contact-label">
                  <FiPhone size={14} className="ma-contact-icon" aria-hidden="true" />
                  {english ? "Sales Office:" : "دفتر فروش مرکزی:"}
                </span>
                <a href={`tel:${toAsciiPhone(displayPhone(phone))}`} dir="ltr" className="ma-contact-value">
                  {displayPhone(phone)}
                </a>
              </div>
              {factoryPhone && (
                <div className="ma-contact-item">
                  <span className="ma-contact-label">
                    <FiPhone size={14} className="ma-contact-icon" aria-hidden="true" />
                    {english ? "Factory:" : "کارخانه مرکزی:"}
                  </span>
                  <a href={`tel:${toAsciiPhone(displayPhone(factoryPhone))}`} dir="ltr" className="ma-contact-value">
                    {displayPhone(factoryPhone)}
                  </a>
                </div>
              )}
              {email && (
                <div className="ma-contact-item">
                  <span className="ma-contact-label">
                    <FiMail size={14} className="ma-contact-icon" aria-hidden="true" />
                    {english ? "Email:" : "پست الکترونیکی:"}
                  </span>
                  <a href={`mailto:${email}`} dir="ltr" className="ma-contact-value">
                    {email}
                  </a>
                </div>
              )}
            </div>
          </section>

          {/* Column 2: Products & Purchase */}
          <FooterAccordionCol
            title={english ? "Products & Catalog" : "خرید و محصولات"}
            id="footer-products-title"
            links={productLinks}
            english={english}
          />

          {/* Column 3: Corporate Sales & Customer Portal */}
          <FooterAccordionCol
            title={english ? "Corporate Services" : "خدمات و فروش سازمانی"}
            id="footer-service-title"
            links={serviceLinks}
            english={english}
          />

          {/* Column 4: Corporate & Content */}
          <FooterAccordionCol
            title={english ? "About Mehr Asl" : "درباره مهر اصل"}
            id="footer-company-links-title"
            links={companyLinks}
            english={english}
          />

          {/* Column 5: Location & Authentications */}
          <section className="footer-col" aria-labelledby="footer-location-title">
            <h2 className="footer-col-title" id="footer-location-title">
              {english ? "Location & Authentications" : "نشانی و مجوزها"}
            </h2>
            <div className="ma-address-box">
              <strong>
                <FiMapPin size={15} aria-hidden="true" style={{ color: "#2ecc71" }} />
                {english ? "Central Office:" : "دفتر مرکزی:"}
              </strong>
              <p>{address}</p>
            </div>
            <div className="ma-badges">
              {badges.map((badge) => {
                const validUrl = /^https?:\/\//i.test(badge.url);
                return (
                  <div key={badge.id} className="ma-badge-item">
                    {badge.image ? (
                      validUrl ? (
                        <a href={badge.url} target="_blank" rel="noreferrer" title={badge.title}>
                          <Image src={badge.image} alt={badge.alt || badge.title} width={80} height={60} sizes="80px" />
                        </a>
                      ) : (
                        <Image src={badge.image} alt={badge.alt || badge.title} width={80} height={60} sizes="80px" />
                      )
                    ) : (
                      <span>{badge.title}</span>
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        </div>

        {/* Footer Bottom Utility Bar */}
        <div className="footer-bottom">
          <div className="footer-bottom-inner">
            <p className="footer-copyright-text">
              © {copyright}
            </p>
            <div className="ma-socials" aria-label={english ? "Social media links" : "شبکه‌های اجتماعی"}>
              <a href="https://wa.me/" target="_blank" rel="noreferrer" className="ma-social-btn" title="واتساپ" aria-label="WhatsApp">
                <FaWhatsapp size={16} aria-hidden="true" />
              </a>
              <a href="https://t.me/" target="_blank" rel="noreferrer" className="ma-social-btn" title="تلگرام" aria-label="Telegram">
                <FaTelegramPlane size={16} aria-hidden="true" />
              </a>
              <a href="https://linkedin.com/" target="_blank" rel="noreferrer" className="ma-social-btn" title="لینکدین" aria-label="LinkedIn">
                <FaLinkedinIn size={16} aria-hidden="true" />
              </a>
              <a href="https://instagram.com/" target="_blank" rel="noreferrer" className="ma-social-btn" title="اینستاگرام" aria-label="Instagram">
                <FaInstagram size={16} aria-hidden="true" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
