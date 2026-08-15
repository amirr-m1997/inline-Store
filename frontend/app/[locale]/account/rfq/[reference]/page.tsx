import type { Metadata } from "next";
import { AccountRfqDetail } from "../../../../../components/account/account-rfq";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../../../../lib/locale-url";

export async function generateMetadata({ params }: { params: Promise<{ locale: string; reference: string }> }): Promise<Metadata> { const { locale } = await params; const path = "/account/rfq"; return { title: locale === "en" ? "RFQ details" : "جزئیات استعلام قیمت", robots: { index: false, follow: false }, alternates: { canonical: absoluteUrl(localizedPath(locale, path)), ...localizedAlternates(path) } }; }
export default async function AccountRfqDetailPage({ params }: { params: Promise<{ locale: string; reference: string }> }) { const { reference } = await params; return <AccountRfqDetail reference={decodeURIComponent(reference)} />; }
