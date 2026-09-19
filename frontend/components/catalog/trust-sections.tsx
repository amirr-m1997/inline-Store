import Image from "next/image";
import Link from "next/link";

export type CompanyCertification = {
  id: number; title_fa: string; title_en: string; issuer: string; certificate_code: string;
  file: string | null; image: string | null; issued_date: string | null; expiry_date: string | null;
  verification_status: string; order: number;
};

export type CompanyHonor = {
  id: number; title_fa: string; title_en: string; issuer: string; year_label: string;
  description_fa: string; description_en: string; image: string | null; file: string | null; order: number;
};

function pick(locale: string, fa: string, en: string) {
  return locale === "en" && en ? en : fa;
}

function CertificationCard({ locale, item }: { locale: string; item: CompanyCertification }) {
  const english = locale === "en";
  const title = pick(locale, item.title_fa, item.title_en) || item.title_fa;
  const body = <>{item.image ? <span className="trust-cert-media"><Image src={item.image} alt={title} width={120} height={90} loading="lazy" /></span> : <span className="trust-cert-badge" aria-hidden="true">✓</span>}<div><h3>{title}</h3>{item.issuer && <p>{item.issuer}</p>}{item.certificate_code && <small>{english ? "Certificate" : "سند"}: <bdi dir="ltr">{item.certificate_code}</bdi></small>}</div></>;
  return item.file ? <a className="trust-cert-card" href={item.file} target="_blank" rel="noreferrer" aria-label={`${title} — ${english ? "view document" : "مشاهده سند"}`}>{body}</a> : <article className="trust-cert-card">{body}</article>;
}

export function TrustSections({ locale, companyName, certifications, honors }: { locale: string; companyName: string; certifications: CompanyCertification[]; honors: CompanyHonor[] }) {
  const english = locale === "en";
  const steps = english ? [
    ["01", "Submit your inquiry", "Send the parts list or technical specification."],
    ["02", "Technical review", "Our engineers verify compatibility and equivalents."],
    ["03", "Official quotation", "Receive a transparent, itemized proforma invoice."],
    ["04", "Trackable supply", "Follow your order from confirmation to delivery."],
  ] : [
    ["۰۱", "ثبت درخواست", "فهرست قطعات یا مشخصات فنی را ارسال کنید."],
    ["۰۲", "بررسی فنی", "کارشناسان ما سازگاری و جایگزین‌ها را بررسی می‌کنند."],
    ["۰۳", "پیش‌فاکتور رسمی", "پیش‌فاکتور شفاف و قلم‌به‌قلم دریافت کنید."],
    ["۰۴", "تأمین قابل پیگیری", "سفارش را از تأیید تا تحویل دنبال کنید."],
  ];
  return <>
    {(certifications.length > 0 || honors.length > 0) && <section className="enterprise-section home-trust site-container" aria-labelledby="home-trust-title">
      <header className="home-section-heading mehrasl-section-heading"><div><div className="section-kicker">{english ? "Verified credentials" : "اعتبار تأییدشده"}</div><h2 id="home-trust-title">{english ? `Why trust ${companyName}?` : `چرا به ${companyName} اعتماد کنیم؟`}</h2></div><Link className="mehrasl-text-link" href={`/${locale}/about`}>{english ? "About us" : "درباره ما"} <span aria-hidden="true" className="rtl:rotate-180 inline-block">←</span></Link></header>
      {certifications.length > 0 && <div className="trust-cert-grid">{certifications.slice(0, 4).map((item) => <CertificationCard key={item.id} locale={locale} item={item} />)}</div>}
      {honors.length > 0 && <ul className="trust-honor-list">{honors.slice(0, 4).map((item) => <li key={item.id}><strong>{item.year_label}</strong><div><h3>{pick(locale, item.title_fa, item.title_en) || item.title_fa}</h3>{item.issuer && <p>{item.issuer}</p>}</div></li>)}</ul>}
    </section>}
    <section className="enterprise-section home-process site-container" aria-labelledby="home-process-title">
      <header className="home-section-heading mehrasl-section-heading"><div><div className="section-kicker">{english ? "B2B procurement path" : "مسیر خرید سازمانی"}</div><h2 id="home-process-title">{english ? "From inquiry to delivery in four steps" : "از درخواست تا تحویل در چهار گام"}</h2></div></header>
      <ol className="home-process-steps">{steps.map(([number, title, text]) => <li key={number}><span aria-hidden="true">{number}</span><h3>{title}</h3><p>{text}</p></li>)}</ol>
      <div className="home-process-actions"><Link className="site-hero-button primary" href={`/${locale}/rfq`}>{english ? "Request a Quote" : "درخواست پیش‌فاکتور"}</Link><Link className="site-hero-button secondary" href={`/${locale}/contact`}>{english ? "Talk to Sales" : "گفت‌وگو با فروش"}</Link></div>
    </section>
  </>;
}
