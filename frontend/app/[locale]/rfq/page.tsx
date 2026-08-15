import type { Metadata } from "next";
import { RfqForm } from "../../../components/rfq/rfq-form";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../../lib/locale-url";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const path = "/rfq";
  return { title: locale === "en" ? "Request for Quotation" : "استعلام قیمت", description: locale === "en" ? "Submit a request for quotation for industrial products." : "درخواست استعلام قیمت محصولات صنعتی.", robots: { index: false, follow: true }, alternates: { canonical: absoluteUrl(localizedPath(locale, path)), ...localizedAlternates(path) } };
}

export default async function RfqPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const english = locale === "en";
  return <main className="rfq-page site-container" dir={english ? "ltr" : "rtl"}><header className="content-index-heading"><span>{english ? "Customer Service" : "امور مشتریان"}</span><h1>{english ? "Request for Quotation" : "استعلام قیمت"}</h1><p>{english ? "Share your product and business requirements for review. This request is received for review and is not a quotation or an order." : "نیاز محصول و کسب‌وکار خود را برای بررسی ارسال کنید. این درخواست برای بررسی دریافت می‌شود و به معنی پیش‌فاکتور یا سفارش نیست."}</p></header><RfqForm /></main>;
}
