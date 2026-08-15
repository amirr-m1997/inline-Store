import type { Metadata } from "next";
import { AccountRfqHistory } from "../../../../components/account/account-rfq";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../../../lib/locale-url";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> { const { locale } = await params; const path = "/account/rfq"; return { title: locale === "en" ? "My RFQs" : "استعلام‌های قیمت من", robots: { index: false, follow: false }, alternates: { canonical: absoluteUrl(localizedPath(locale, path)), ...localizedAlternates(path) } }; }
export default function AccountRfqPage() { return <AccountRfqHistory />; }
