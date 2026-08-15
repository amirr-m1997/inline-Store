"use client";

import { useState } from "react";
import { FormField } from "../ui/form-field";
import { Input } from "../ui/input";
import { sendContact } from "../../lib/api/content";

type ContactFormValues = { full_name: string; phone: string; email: string; subject: string; message: string };
const initialForm: ContactFormValues = { full_name: "", phone: "", email: "", subject: "", message: "" };

export function ContactForm() {
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const field = (name: keyof ContactFormValues, value: string) => setForm((current) => ({ ...current, [name]: value }));
  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setLoading(true); setError(""); setSuccess("");
    try { const data = await sendContact<{ detail: string }>(form); setSuccess(data.detail); setForm(initialForm); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "ثبت پیام ناموفق بود."); }
    finally { setLoading(false); }
  };
  return <form className="contact-form" onSubmit={submit} aria-labelledby="contact-form-title">
    <h2 id="contact-form-title">ارسال پیام</h2>
    <p className="contact-form-intro">موضوع و اطلاعات تماس خود را وارد کنید تا پیام شما برای بررسی ثبت شود.</p>
    <div>
      <FormField label="نام و نام خانوادگی" required><Input value={form.full_name} onChange={(event) => field("full_name", event.target.value)} autoComplete="name" maxLength={255} required /></FormField>
      <label htmlFor="contact-phone">شماره تماس *<input id="contact-phone" value={form.phone} onChange={(event) => field("phone", event.target.value)} dir="ltr" inputMode="tel" autoComplete="tel" maxLength={64} required /></label>
      <label htmlFor="contact-email">ایمیل<input id="contact-email" value={form.email} onChange={(event) => field("email", event.target.value)} type="email" dir="ltr" autoComplete="email" /></label>
      <label htmlFor="contact-subject">موضوع *<input id="contact-subject" value={form.subject} onChange={(event) => field("subject", event.target.value)} maxLength={255} required /></label>
      <label className="contact-message-field" htmlFor="contact-message">پیام *<textarea id="contact-message" value={form.message} onChange={(event) => field("message", event.target.value)} maxLength={5000} required /></label>
    </div>
    {error && <p className="form-error" role="alert">{error}</p>}
    {success && <p className="form-success" role="status" aria-live="polite">{success}</p>}
    <button className="btn-primary" type="submit" disabled={loading}>{loading ? "در حال ارسال…" : "ثبت پیام"}</button>
  </form>;
}
