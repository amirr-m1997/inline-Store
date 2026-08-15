import type { Metadata } from "next";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const title = locale === "fa" ? "ورود به حساب کاربری" : "Sign in";
  return { title, description: title };
}

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return children;
}
