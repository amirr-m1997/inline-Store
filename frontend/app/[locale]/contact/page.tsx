import type { Metadata } from "next";
import Link from "next/link";
import { ContactForm } from "../../../components/content/contact-form";
import { getCompanyServer } from "../../../lib/api/content";
import type { CompanyInfo } from "../../../types/api";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../../lib/locale-url";

type Params = { locale: string };

async function loadCompany() { return getCompanyServer<CompanyInfo>().catch(() => null); }

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { locale } = await params;
  const company = await loadCompany();
  const title = company?.name_fa ? `تماس با ${company.name_fa}` : "تماس با ما";
  const description = company?.description || undefined;
  const path = "/contact";
  return { title, description, alternates: { canonical: absoluteUrl(localizedPath(locale, path)), ...localizedAlternates(path) }, openGraph: { title, description, url: absoluteUrl(localizedPath(locale, path)), locale: locale === "en" ? "en_US" : "fa_IR", type: "website" } };
}

function ContactInformation({ company }: { company: CompanyInfo | null }) {
  const items = [
    company?.phone ? <a key="phone" href={`tel:${company.phone}`}><i aria-hidden="true">☎</i><span><small>تلفن</small><b dir="ltr">{company.phone}</b></span></a> : null,
    company?.mobile ? <a key="mobile" href={`tel:${company.mobile}`}><i aria-hidden="true">◉</i><span><small>موبایل</small><b dir="ltr">{company.mobile}</b></span></a> : null,
    company?.email ? <a key="email" href={`mailto:${company.email}`}><i aria-hidden="true">✉</i><span><small>ایمیل</small><b dir="ltr">{company.email}</b></span></a> : null,
    company?.address ? <div key="address"><i aria-hidden="true">⌖</i><span><small>نشانی</small><b>{company.address}</b></span></div> : null,
    company?.website ? <a key="website" href={company.website} target="_blank" rel="noreferrer"><i aria-hidden="true">↗</i><span><small>وب‌سایت</small><b dir="ltr">{company.website}</b></span></a> : null,
    company?.working_hours ? <div key="hours"><i aria-hidden="true">◷</i><span><small>ساعات کاری</small><b>{company.working_hours}</b></span></div> : null,
  ].filter(Boolean);
  return <aside className="contact-information" aria-labelledby="contact-information-title"><h2 id="contact-information-title">اطلاعات تماس</h2>{items.length ? items : <p>اطلاعات تماس شرکت هنوز ثبت نشده است.</p>}</aside>;
}

export default async function ContactPage({ params }: { params: Promise<Params> }) {
  const { locale } = await params;
  const company = await loadCompany();
  return <main className="public-page site-container">
    <nav className="public-breadcrumb" aria-label="مسیر صفحه"><Link href={`/${locale}`}>خانه</Link><span aria-hidden="true">/</span><b>تماس با ما</b></nav>
    <header className="contact-heading"><span>ارتباط مستقیم</span><h1>تماس با {company?.name_fa || "ما"}</h1>{company?.description && <p>{company.description}</p>}<div className="contact-heading-actions"><Link className="btn-secondary" href={`/${locale}/shop`}>مشاهده محصولات</Link></div></header>
    <div className="contact-layout"><ContactInformation company={company} /><ContactForm /></div>
  </main>;
}
