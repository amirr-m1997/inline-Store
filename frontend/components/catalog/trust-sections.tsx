import Link from "next/link";
import { FiClipboard, FiFileText, FiSearch, FiTruck } from "react-icons/fi";
import type { IconType } from "react-icons";

export type CompanyCertification = {
  id: number; title_fa: string; title_en: string; issuer: string; certificate_code: string;
  file: string | null; image: string | null; issued_date: string | null; expiry_date: string | null;
  verification_status: string; order: number;
};

export type CompanyHonor = {
  id: number; title_fa: string; title_en: string; issuer: string; year_label: string;
  description_fa: string; description_en: string; image: string | null; file: string | null; order: number;
};

export function TrustSections({ locale }: { locale: string }) {
  const english = locale === "en";
  const steps: Array<[IconType, string, string]> = english ? [
    [FiClipboard, "Submit your inquiry", "Send the parts list or technical specification."],
    [FiSearch, "Technical review", "Our engineers verify compatibility and equivalents."],
    [FiFileText, "Official quotation", "Receive a transparent, itemized proforma invoice."],
    [FiTruck, "Trackable supply", "Follow your order from confirmation to delivery."],
  ] : [
    [FiClipboard, "ثبت درخواست", "فهرست قطعات یا مشخصات فنی را ارسال کنید."],
    [FiSearch, "بررسی فنی", "کارشناسان ما سازگاری و جایگزین‌ها را بررسی می‌کنند."],
    [FiFileText, "استعلام قیمت", "استعلام قیمت شفاف و قلم‌به‌قلم دریافت کنید."],
    [FiTruck, "تأمین قابل پیگیری", "سفارش را از تأیید تا تحویل دنبال کنید."],
  ];
  return <section className="enterprise-section home-process site-container" aria-labelledby="home-process-title">
      <header className="home-section-heading mehrasl-section-heading"><div><div className="section-kicker">{english ? "B2B procurement path" : "مسیر خرید سازمانی"}</div><h2 id="home-process-title">{english ? "From inquiry to delivery in four steps" : "از درخواست تا تحویل در چهار گام"}</h2></div></header>
      <ol className="home-process-steps">{steps.map(([Icon, title, text]) => <li key={title}><span className="home-process-step-icon" aria-hidden="true"><Icon /></span><h3>{title}</h3><p>{text}</p></li>)}</ol>
      <div className="home-process-actions"><Link className="site-hero-button primary" href={`/${locale}/rfq`}>{english ? "Request a Quote" : "استعلام قیمت"}</Link><Link className="site-hero-button secondary" href={`/${locale}/contact`}>{english ? "Talk to Sales" : "گفت‌وگو با فروش"}</Link></div>
    </section>;
}
