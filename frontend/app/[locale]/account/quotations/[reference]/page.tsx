import type { Metadata } from "next";
import { AccountQuotation } from "../../../../../components/account/account-quotation";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../../../../lib/locale-url";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> { const { locale } = await params; const path = "/account/quotations"; return { title: locale === "en" ? "Quotation" : "پیشنهاد قیمت", robots: { index: false, follow: false }, alternates: { canonical: absoluteUrl(localizedPath(locale, path)), ...localizedAlternates(path) } }; }
export default async function AccountQuotationPage({ params }: { params: Promise<{ locale: string; reference: string }> }) { const { reference } = await params; return <AccountQuotation reference={decodeURIComponent(reference)} />; }
