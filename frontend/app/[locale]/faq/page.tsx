import type { Metadata } from "next";
import Link from "next/link";
import { FAQList, faqTypes } from "../../../components/content/editorial";
import { getFAQsServer } from "../../../lib/api/content";
import type { FAQEntry } from "../../../types/api";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../../lib/locale-url";

type Props = { params: Promise<{ locale: string }>; searchParams: Promise<{ type?: string | string[] }> };
const valueOf = (value?: string | string[]) => Array.isArray(value) ? value[0] || "" : value || "";

function faqSchema(faqs: FAQEntry[], locale: string) {
  return { "@context": "https://schema.org", "@type": "FAQPage", mainEntity: faqs.map((faq) => ({ "@type": "Question", name: locale === "en" && faq.question_en ? faq.question_en : faq.question_fa, acceptedAnswer: { "@type": "Answer", text: locale === "en" && faq.answer_en ? faq.answer_en : faq.answer_fa } })) };
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params; const english = locale === "en"; const path = "/faq";
  const faqs = await getFAQsServer({}).catch(() => [] as FAQEntry[]);
  return { title: english ? "Frequently Asked Questions" : "سوالات متداول", description: english ? "Published technical and customer-service questions for Mehrasl products and services." : "پاسخ‌های منتشرشده به پرسش‌های فنی و امور مشتریان مهراصل.", robots: faqs.length ? undefined : { index: false, follow: true }, alternates: { canonical: absoluteUrl(localizedPath(locale, path)), ...localizedAlternates(path) } };
}

export default async function FAQPage({ params, searchParams }: Props) {
  const { locale } = await params; const type = valueOf((await searchParams).type); const faqs = await getFAQsServer(type ? { type } : {}).catch(() => [] as FAQEntry[]); const english = locale === "en"; const title = english ? "Frequently Asked Questions" : "سوالات متداول";
  const schema = faqs.length ? faqSchema(faqs, locale) : null;
  return <>{schema && <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema).replace(/</g, "\\u003c") }} />}<main className="faq-page site-container"><nav className="public-breadcrumb" aria-label={english ? "Breadcrumb" : "مسیر صفحه"}><Link href={`/${locale}`}>{english ? "Home" : "خانه"}</Link><span aria-hidden="true">/</span><b>{title}</b></nav><header className="content-index-heading"><span>{english ? "Technical knowledge" : "دانش فنی"}</span><h1>{title}</h1><p>{english ? "Find concise answers to published product, technical and customer-service questions." : "پاسخ‌های کوتاه و ساختاریافته برای پرسش‌های منتشرشده درباره محصول، مسائل فنی و امور مشتریان."}</p></header><nav className="faq-type-nav" aria-label={english ? "FAQ types" : "نوع سوالات متداول"}>{faqTypes.map((item) => <Link key={item.value || "all"} className={type === item.value ? "is-active" : undefined} href={item.value ? `/${locale}/faq?type=${item.value}` : `/${locale}/faq`} aria-current={type === item.value ? "page" : undefined}>{english ? item.en : item.fa}</Link>)}</nav>{faqs.length ? <FAQList faqs={faqs} locale={locale} /> : <section className="faq-empty" aria-live="polite"><h2>{english ? "No published questions are available yet." : "هنوز سوال منتشرشده‌ای در دسترس نیست."}</h2><p>{english ? "Please check the Knowledge Center for published technical content." : "برای محتوای فنی منتشرشده، مرکز دانش را ببینید."}</p><Link href={`/${locale}/knowledge`}>{english ? "Open Knowledge & News" : "مشاهده دانش و اخبار"}</Link></section>}</main></>;
}
