"use client";

import Link from "next/link";
import { useState } from "react";
import { useCompanyInfo } from "../../../hooks/use-company-info";

type ContactForm = { full_name: string; phone: string; email: string; subject: string; message: string };
const initialForm: ContactForm = { full_name: "", phone: "", email: "", subject: "", message: "" };

export default function ContactPage() {
  const company = useCompanyInfo();
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const field = (name: keyof ContactForm, value: string) => setForm((current) => ({ ...current, [name]: value }));
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setLoading(true); setError(""); setSuccess("");
    const response = await fetch("/api/v1/site/contact/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form) });
    const data = await response.json().catch(() => ({})); setLoading(false);
    if (!response.ok) { setError(Object.values(data).flat().join(" ") || "ثبت پیام ناموفق بود."); return; }
    setSuccess(data.detail); setForm(initialForm);
  };
  return <main className="public-page site-container">
    <nav className="public-breadcrumb"><Link href="/fa">خانه</Link><span>/</span><b>تماس با ما</b></nav>
    <header className="contact-heading"><span>ارتباط مستقیم</span><h1>تماس با {company?.name_fa || "شرکت"}</h1><p>برای دریافت راهنمایی درباره محصولات، موجودی و فرایند خرید، پیام خود را برای کارشناسان ما ارسال کنید.</p></header>
    <div className="contact-layout">
      <aside className="contact-information"><h2>اطلاعات تماس</h2>{company?.phone && <a href={`tel:${company.phone}`}><i>☎</i><span><small>تلفن</small><b dir="ltr">{company.phone}</b></span></a>}{company?.mobile && <a href={`tel:${company.mobile}`}><i>◉</i><span><small>موبایل</small><b dir="ltr">{company.mobile}</b></span></a>}{company?.email && <a href={`mailto:${company.email}`}><i>✉</i><span><small>ایمیل</small><b dir="ltr">{company.email}</b></span></a>}{company?.address && <div><i>⌖</i><span><small>نشانی</small><b>{company.address}</b></span></div>}{company?.working_hours && <div><i>◷</i><span><small>ساعات کاری</small><b>{company.working_hours}</b></span></div>}<p>نقشه پس از ثبت نشانی مکانی معتبر در تنظیمات شرکت نمایش داده خواهد شد.</p></aside>
      <form className="contact-form" onSubmit={submit}><h2>ارسال پیام</h2><div><label>نام و نام خانوادگی *<input value={form.full_name} onChange={(event) => field("full_name", event.target.value)} autoComplete="name" maxLength={255} required /></label><label>شماره تماس *<input value={form.phone} onChange={(event) => field("phone", event.target.value)} dir="ltr" inputMode="tel" autoComplete="tel" maxLength={64} required /></label><label>ایمیل<input value={form.email} onChange={(event) => field("email", event.target.value)} type="email" dir="ltr" autoComplete="email" /></label><label>موضوع *<input value={form.subject} onChange={(event) => field("subject", event.target.value)} maxLength={255} required /></label><label className="contact-message-field">پیام *<textarea value={form.message} onChange={(event) => field("message", event.target.value)} maxLength={5000} required /></label></div>{error && <p className="form-error" role="alert">{error}</p>}{success && <p className="form-success" role="status">{success}</p>}<button className="btn-primary" disabled={loading}>{loading ? "در حال ارسال…" : "ارسال پیام"}</button></form>
    </div>
  </main>;
}
