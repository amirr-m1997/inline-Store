import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { getAdvantagesServer, getCapabilitiesServer, getCompanyCertificationsServer, getCompanyHonorsServer, getCompanyLocationsServer, getCompanyMilestonesServer, getCompanySectionsServer, getCompanyServer } from "../../../lib/api/content";
import type { CompanyInfo } from "../../../types/api";
import type { Advantage } from "../../../components/catalog/company-advantages";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../../lib/locale-url";
import { CompanyTimeline } from "../../../components/content/company-timeline";
import { CompanyLocationGroups } from "../../../components/content/company-location-groups";
import { CompanyCertificationCards, CompanyHonorCards } from "../../../components/content/company-records";

type Params = { locale: string };

async function loadAboutData() {
  const [company, advantages, sections, milestones, locations, capabilities, certifications, honors] = await Promise.all([
    getCompanyServer<CompanyInfo>().catch(() => null),
    getAdvantagesServer<Advantage[]>().catch(() => []),
    getCompanySectionsServer<CompanySection[]>().catch(() => []),
    getCompanyMilestonesServer<CompanyMilestone[]>().catch(() => []),
    getCompanyLocationsServer<CompanyLocation[]>().catch(() => []),
    getCapabilitiesServer<Capability[]>().catch(() => []),
    getCompanyCertificationsServer<Certification[]>().catch(() => []),
    getCompanyHonorsServer<Honor[]>().catch(() => []),
  ]);
  return { company, advantages, sections, milestones, locations, capabilities, certifications, honors };
}

type CompanySection = { id: number; section_type: string; title_fa: string; title_en: string; summary_fa: string; summary_en: string; body_fa: string; body_en: string; image: string | null; order: number };
type CompanyMilestone = { id: number; date_label: string; title_fa: string; title_en: string; description_fa: string; description_en: string };
type CompanyLocation = { id: number; location_type: string; name_fa: string; name_en: string; address_fa: string; address_en: string; phone: string; mobile: string; email: string; working_hours: string };
type Capability = { id: number; slug: string; title_fa: string; title_en: string; summary_fa: string; summary_en: string };
type Certification = { id: number; title_fa: string; title_en: string; issuer: string; certificate_code: string; file: string | null; verification_status: string };
type Honor = { id: number; title_fa: string; title_en: string; issuer: string; year_label: string; description_fa: string; description_en: string; image: string | null; file: string | null };

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { locale } = await params;
  const company = await getCompanyServer<CompanyInfo>().catch(() => null);
  const title = company?.name_fa ? `درباره ${company.name_fa}` : "درباره ما";
  const description = company?.description || undefined;
  const path = "/about";
  return {
    title,
    description,
    alternates: { canonical: absoluteUrl(localizedPath(locale, path)), ...localizedAlternates(path) },
    openGraph: { title, description, url: absoluteUrl(localizedPath(locale, path)), locale: locale === "en" ? "en_US" : "fa_IR", type: "website" },
  };
}

function ContactDetails({ company }: { company: CompanyInfo }) {
  const details = [
    company.phone ? { label: "تلفن", value: company.phone, href: `tel:${company.phone}`, dir: "ltr" as const } : null,
    company.mobile ? { label: "موبایل", value: company.mobile, href: `tel:${company.mobile}`, dir: "ltr" as const } : null,
    company.email ? { label: "ایمیل", value: company.email, href: `mailto:${company.email}`, dir: "ltr" as const } : null,
    company.address ? { label: "نشانی", value: company.address, href: undefined, dir: undefined } : null,
    company.website ? { label: "وب‌سایت", value: company.website, href: company.website, dir: "ltr" as const } : null,
    company.working_hours ? { label: "ساعات کاری", value: company.working_hours, href: undefined, dir: undefined } : null,
  ].filter((item): item is NonNullable<typeof item> => Boolean(item));
  if (!details.length) return null;
  return <dl className="about-contact-details">{details.map((detail) => <div key={detail.label}><dt>{detail.label}</dt><dd dir={detail.dir}>{detail.href ? <a href={detail.href} target={detail.label === "وب‌سایت" ? "_blank" : undefined} rel={detail.label === "وب‌سایت" ? "noreferrer" : undefined}>{detail.value}</a> : detail.value}</dd></div>)}</dl>;
}

function DemoIndicator({ value, locale }: { value: string; locale: string }) {
  return value.startsWith("[DEMO]") ? <span className="content-demo-indicator" title={locale === "en" ? "Development content" : "محتوای محیط توسعه"}>{locale === "en" ? "Demo" : "نمونه"}</span> : null;
}

export default async function AboutPage({ params }: { params: Promise<Params> }) {
  const { locale } = await params;
  const { company, advantages, sections, milestones, locations, capabilities, certifications, honors } = await loadAboutData();
  const companyName = company?.name_fa || "درباره ما";
  return <main className="public-page site-container">
    <nav className="public-breadcrumb" aria-label={locale === "en" ? "Breadcrumb" : "مسیر صفحه"}><Link href={`/${locale}`}>{locale === "en" ? "Home" : "خانه"}</Link><span aria-hidden="true">/</span><b>{locale === "en" ? "About" : "درباره ما"}</b></nav>
    <section className="about-hero" aria-labelledby="about-title">
      <div><span>{locale === "en" ? "Company profile" : "معرفی مجموعه"}</span><h1 id="about-title">{companyName}</h1>{company?.description && <p>{company.description}</p>}<div><Link className="btn-primary" href={`/${locale}/shop`}>{locale === "en" ? "Browse products" : "مشاهده محصولات"}</Link><Link className="btn-secondary" href={`/${locale}/contact`}>{locale === "en" ? "Contact us" : "تماس با ما"}</Link></div></div>
      {company?.logo && <div className="about-logo"><Image src={company.logo} alt={companyName} width={240} height={180} sizes="(max-width: 700px) 160px, 240px" /></div>}
    </section>
    {sections.length > 0 && <section className="about-content-sections about-content-sections--editorial" aria-labelledby="about-content-title"><header><span>{locale === "en" ? "Published company information" : "اطلاعات منتشرشده شرکت"}</span><h2 id="about-content-title">{locale === "en" ? "About the company" : "درباره این مجموعه"}</h2></header><div>{sections.slice(0, 4).map((section) => { const title = locale === "en" && section.title_en ? section.title_en : section.title_fa; const summary = locale === "en" && section.summary_en ? section.summary_en : section.summary_fa; const body = locale === "en" && section.body_en ? section.body_en : section.body_fa; if (!title && !summary && !body && !section.image) return null; return <article key={section.id}>{section.image && <Image src={section.image} alt={title || companyName} width={480} height={280} />}{title && <h3>{title} <DemoIndicator value={title} locale={locale} /></h3>}{summary && <p className="section-summary">{summary}</p>}{body && <p>{body}</p>}</article>; })}</div></section>}
    <CompanyTimeline milestones={milestones} locale={locale} />
    {locations.length > 0 && <section className="about-preview-section" aria-labelledby="about-locations-title"><header><span>{locale === "en" ? "Company presence" : "مراکز شرکت"}</span><h2 id="about-locations-title">{locale === "en" ? "Facilities and offices" : "مراکز و دفاتر"}</h2><p>{locale === "en" ? "A concise view of the published company locations." : "مروری کوتاه بر مراکز منتشرشده شرکت."}</p></header><CompanyLocationGroups locations={locations.slice(0, 3)} locale={locale} showHeader={false} compact /><Link className="btn-secondary" href={`/${locale}/locations`}>{locale === "en" ? "View all locations" : "مشاهده همه مراکز"}</Link></section>}
    {capabilities.length > 0 && <section className="about-content-sections about-content-sections--capabilities" aria-labelledby="about-capabilities-title"><header><span>{locale === "en" ? "Published capabilities" : "توانمندی‌های منتشرشده"}</span><h2 id="about-capabilities-title">{locale === "en" ? "Capabilities" : "توانمندی‌ها"}</h2></header><div>{capabilities.slice(0, 3).map((item) => <article key={item.id}><h3><Link href={`/${locale}/capabilities/${item.slug}`}>{locale === "en" && item.title_en ? item.title_en : item.title_fa}</Link> <DemoIndicator value={locale === "en" && item.title_en ? item.title_en : item.title_fa} locale={locale} /></h3>{(locale === "en" ? item.summary_en || item.summary_fa : item.summary_fa) && <p>{locale === "en" ? item.summary_en || item.summary_fa : item.summary_fa}</p>}</article>)}</div><Link className="btn-secondary" href={`/${locale}/capabilities`}>{locale === "en" ? "View all capabilities" : "مشاهده همه توانمندی‌ها"}</Link></section>}
    {advantages.length > 0 && <section className="about-values" aria-labelledby="about-advantages-title"><header><span>{locale === "en" ? "Recorded company information" : "آنچه در اطلاعات شرکت ثبت شده است"}</span><h2 id="about-advantages-title">{locale === "en" ? "Company strengths" : "مزیت‌های مجموعه"}</h2></header><div>{advantages.map((item) => <article key={item.id}><i aria-hidden="true">{item.icon || "✓"}</i><h3>{locale === "en" && item.title_en ? item.title_en : item.title_fa}</h3>{(locale !== "en" || item.description_en || item.description_fa) && (locale === "en" ? item.description_en || item.description_fa : item.description_fa) && <p>{locale === "en" ? item.description_en || item.description_fa : item.description_fa}</p>}</article>)}</div></section>}
    <CompanyCertificationCards items={certifications} locale={locale} />
    <CompanyHonorCards items={honors} locale={locale} />
    {company && <section className="about-contact-summary" aria-labelledby="about-contact-title"><div><span>{locale === "en" ? "Direct contact" : "ارتباط مستقیم"}</span><h2 id="about-contact-title">{locale === "en" ? "Contact the company" : "اطلاعات تماس شرکت"}</h2><Link className="btn-secondary" href={`/${locale}/contact`}>{locale === "en" ? "Send a message" : "ارسال پیام"}</Link></div><ContactDetails company={company} /></section>}
  </main>;
}
