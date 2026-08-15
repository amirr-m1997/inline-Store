import type { Metadata } from "next";
import { AccountSupportCenter } from "../../../../components/account/account-support-center";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../../../lib/locale-url";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const path = "/account/support";
  return { title: locale === "en" ? "Account support" : "پشتیبانی حساب", description: locale === "en" ? "Private support history for your account." : "سوابق خصوصی پشتیبانی حساب کاربری.", robots: { index: false, follow: false }, alternates: { canonical: absoluteUrl(localizedPath(locale, path)), ...localizedAlternates(path) } };
}

export default function AccountSupportPage() { return <AccountSupportCenter />; }
