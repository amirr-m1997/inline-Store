"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { getProduct, type ProductDetail } from "../../lib/api/products";
import { getOrder } from "../../lib/api/orders";
import { submitSupport } from "../../lib/api/content";

type OrderContext = { id: number; order_number: string; created_at: string; status_label: string };
const requestTypes: Record<string, [string, string]> = { complaint: ["شکایت", "Complaint"], product_support: ["پشتیبانی محصول", "Product support"], order_support: ["پشتیبانی سفارش", "Order support"], warranty: ["گارانتی", "Warranty"], sales: ["فروش", "Sales"], other: ["سایر", "Other"] };

export function SupportRequestForm({ english = false }: { english?: boolean }) {
  const { locale = "fa" } = useParams<{ locale: string }>();
  const params = useSearchParams();
  const t = (fa: string, en: string) => english ? en : fa;
  const [form, setForm] = useState({ request_type: "other", full_name: "", phone: "", email: "", subject: "", message: "" });
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [order, setOrder] = useState<OrderContext | null>(null);
  const [contextError, setContextError] = useState(false);
  const [busy, setBusy] = useState(false); const [error, setError] = useState(""); const [reference, setReference] = useState("");

  useEffect(() => {
    const productSlug = params.get("product"); const orderId = params.get("order");
    setContextError(false); setProduct(null); setOrder(null);
    if (productSlug) getProduct(productSlug).then(setProduct).catch(() => setContextError(true));
    if (orderId && /^\d+$/.test(orderId)) getOrder<OrderContext>(orderId).then(setOrder).catch(() => setContextError(true));
    else if (orderId) setContextError(true);
  }, [params]);
  const change = (key: keyof typeof form, value: string) => setForm({ ...form, [key]: value });
  async function submit(event: React.FormEvent) { event.preventDefault(); setBusy(true); setError(""); try { const result = await submitSupport<{ reference: string }>({ ...form, ...(product ? { product: product.id } : {}), ...(order ? { order: order.id } : {}) }); setReference(result.reference); } catch { setError(t("ثبت درخواست ناموفق بود.", "The request could not be submitted.")); } finally { setBusy(false); } }
  const clearContext = (key: "product" | "order") => { if (key === "product") setProduct(null); else setOrder(null); };
  return <div className="support-request-stack">
    {contextError && <p className="form-error" role="alert">{t("زمینه انتخاب‌شده در دسترس نیست؛ می‌توانید درخواست عمومی ثبت کنید.", "The selected context is unavailable; you can still submit a general request.")}</p>}
    {(product || order) && <section className="support-context" aria-labelledby="support-context-title"><h2 id="support-context-title">{t("موضوع درخواست", "Request context")}</h2>{product && <div><p><b>{product.name_fa}</b><small><bdi dir="ltr">{product.sku || product.id}</bdi></small></p><button type="button" onClick={() => clearContext("product")}>{t("حذف محصول", "Remove product")}</button></div>}{order && <div><p><bdi dir="ltr">{order.order_number}</bdi><small>{order.status_label}</small></p><button type="button" onClick={() => clearContext("order")}>{t("حذف سفارش", "Remove order")}</button></div>}</section>}
    {reference && <section className="form-success" role="status"><h2>{t("درخواست شما دریافت شد", "Your support request was received")}</h2><p>{t("کد پیگیری:", "Reference:")} <code dir="ltr">{reference}</code></p></section>}
    <form className="contact-form" onSubmit={submit} aria-labelledby="support-request-form-title"><h2 id="support-request-form-title">{t("ثبت درخواست پشتیبانی", "Submit a support request")}</h2><label>{t("نوع درخواست", "Request type")}<select value={form.request_type} onChange={e => change("request_type", e.target.value)}>{Object.entries(requestTypes).map(([value, labels]) => <option key={value} value={value}>{t(...labels)}</option>)}</select></label><label>{t("نام و نام خانوادگی *", "Full name *")}<input required value={form.full_name} onChange={e => change("full_name", e.target.value)} /></label><label>{t("شماره تماس *", "Phone *")}<input required dir="ltr" value={form.phone} onChange={e => change("phone", e.target.value)} /></label><label>{t("ایمیل", "Email")}<input type="email" dir="ltr" value={form.email} onChange={e => change("email", e.target.value)} /></label><label>{t("موضوع *", "Subject *")}<input required value={form.subject} onChange={e => change("subject", e.target.value)} /></label><label className="contact-message-field">{t("پیام *", "Message *")}<textarea required value={form.message} onChange={e => change("message", e.target.value)} /></label>{error && <p role="alert" className="form-error">{error}</p>}<button className="btn-primary" disabled={busy}>{busy ? t("در حال ارسال…", "Submitting…") : t("ارسال درخواست", "Submit request")}</button></form>
    <Link className="support-secondary-link" href={`/${locale}/support`}>{t("بازگشت به پشتیبانی", "Back to support")}</Link>
  </div>;
}
