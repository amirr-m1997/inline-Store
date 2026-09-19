"use client";

import Link from "next/link";

export function FloatingActions({ locale, phone }: { locale: string; phone: string | null }) {
  const english = locale === "en";
  const digits = phone ? phone.replace(/[^+\d]/g, "") : "";
  return <div className="floating-actions" aria-label={english ? "Quick contact" : "تماس سریع"}>
    {digits && <a className="floating-actions-call" href={`tel:${digits}`} aria-label={`${english ? "Call sales" : "تماس با فروش"} ${phone}`}><span aria-hidden="true">☎</span><b>{phone}</b></a>}
    <Link className="floating-actions-quote" href={`/${locale}/rfq`}><span aria-hidden="true">✎</span><b>{english ? "Request Quote" : "پیش‌فاکتور"}</b></Link>
  </div>;
}
