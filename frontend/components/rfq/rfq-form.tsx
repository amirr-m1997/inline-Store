"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { ApiError } from "../../lib/api/client";
import { getProducts, getProduct } from "../../lib/api/products";
import { getRfqCartContext, submitRfq, type RfqCartContextItem, type RfqCreateInput, type RfqRecord } from "../../lib/api/rfq";

type RfqProductContext = RfqCartContextItem;
type RfqLine = { product: RfqProductContext; quantity: number; note: string };
type FormState = { company_name: string; contact_name: string; phone: string; email: string; preferred_contact_method: string; subject: string; message: string };

const emptyForm: FormState = { company_name: "", contact_name: "", phone: "", email: "", preferred_contact_method: "", subject: "", message: "" };

function errorText(value: unknown, english: boolean) {
  if (value instanceof ApiError && value.data && typeof value.data === "object") {
    const data = value.data as Record<string, unknown>;
    const messages = Object.values(data).flatMap((item) => Array.isArray(item) ? item : [item]).filter((item): item is string => typeof item === "string");
    if (messages.length) return messages.join(" ");
  }
  return english ? "The request could not be submitted. Please review the fields and try again." : "ثبت استعلام قیمت ناموفق بود. لطفاً فیلدها را بررسی و دوباره تلاش کنید.";
}

function statusLabel(status: string, english: boolean) {
  const labels: Record<string, [string, string]> = { submitted: ["ثبت‌شده", "Submitted"], under_review: ["در حال بررسی", "Under review"], quoted: ["پیشنهاد صادرشده", "Quote workflow"], closed: ["بسته‌شده", "Closed"], cancelled: ["لغوشده", "Cancelled"] };
  return labels[status]?.[english ? 1 : 0] || status;
}

export function RfqForm() {
  const { locale = "fa" } = useParams<{ locale: string }>();
  const params = useSearchParams();
  const english = locale === "en";
  const t = (fa: string, en: string) => english ? en : fa;
  const [form, setForm] = useState<FormState>(emptyForm);
  const [lines, setLines] = useState<RfqLine[]>([]);
  const [contextLoading, setContextLoading] = useState(false);
  const [contextError, setContextError] = useState(false);
  const [contextWarning, setContextWarning] = useState("");
  const [productQuery, setProductQuery] = useState("");
  const [productResults, setProductResults] = useState<RfqProductContext[]>([]);
  const [searchingProducts, setSearchingProducts] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState<RfqRecord | null>(null);
  const addProductInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const source = params.get("source");
    const slug = params.get("product");
    if (!source && !slug) return;
    setContextLoading(true); setContextError(false); setContextWarning("");
    if (source === "cart") {
      getRfqCartContext().then((context) => {
        setLines(context.items.map((item) => ({ product: item, quantity: item.quantity, note: "" })));
        if (context.omitted_count) setContextWarning(english ? "Some inactive or over-limit cart items were omitted from this request." : "برخی اقلام غیرفعال یا خارج از سقف اقلام بودند و وارد استعلام نشدند.");
      }).catch(() => setContextError(true)).finally(() => setContextLoading(false));
      return;
    }
    if (!slug) return;
    getProduct(slug).then((product) => setLines([{ product: { id: product.id, slug: product.slug, name_fa: product.name_fa, name_en: product.name_en, sku: product.sku, code: product.sku || String(product.id), unit: product.unit, quantity: 1 }, quantity: 1, note: "" }])).catch(() => setContextError(true)).finally(() => setContextLoading(false));
  }, [english, params]);

  const selectedIds = useMemo(() => new Set(lines.map((line) => line.product.id)), [lines]);
  const setField = (field: keyof FormState, value: string) => setForm((current) => ({ ...current, [field]: value }));
  const addProduct = (product: RfqProductContext) => { if (selectedIds.has(product.id)) { setError(t("این محصول قبلاً به استعلام اضافه شده است.", "This product is already in the request.")); addProductInput.current?.focus(); return; } if (lines.length >= 25) { setError(t("حداکثر ۲۵ قلم محصول مجاز است.", "A request can contain up to 25 products.")); addProductInput.current?.focus(); return; } setLines((current) => [...current, { product, quantity: product.quantity || 1, note: "" }]); setProductQuery(""); setProductResults([]); setError(""); };
  const searchProducts = async () => { if (productQuery.trim().length < 2) return; setSearchingProducts(true); setError(""); try { const result = await getProducts({ search: productQuery.trim() }); setProductResults(result.results.filter((item) => !selectedIds.has(item.id)).slice(0, 8).map((item) => ({ id: item.id, slug: item.slug, name_fa: item.name, name_en: item.name, sku: item.code, code: item.code, unit: item.unit, quantity: 1 }))); } catch { setError(t("جستجوی محصول ناموفق بود.", "Product search failed.")); } finally { setSearchingProducts(false); } };
  const updateLine = (id: number, field: "quantity" | "note", value: string) => setLines((current) => current.map((line) => line.product.id === id ? { ...line, [field]: field === "quantity" ? Math.max(1, Math.min(1000000, Number(value.replace(/[^0-9]/g, "")) || 1)) : value } : line));
  const submit = async (event: React.FormEvent) => { event.preventDefault(); if (busy) return; setBusy(true); setError(""); const payload: RfqCreateInput = { ...form, items: lines.map((line) => ({ product: line.product.id, requested_quantity: line.quantity, customer_note: line.note })) }; try { setSuccess(await submitRfq(payload)); } catch (reason) { setError(errorText(reason, english)); } finally { setBusy(false); } };

  if (success) return <section className="rfq-success" role="status" aria-live="polite"><span>{t("استعلام قیمت", "Request for Quotation")}</span><h2>{t("درخواست استعلام قیمت شما ثبت شد.", "Your request for quotation has been submitted.")}</h2><p>{t("درخواست شما برای بررسی دریافت شد؛ این ثبت به‌تنهایی به معنی صدور قیمت یا سفارش نیست.", "Your request was received for review. Submission does not constitute a quotation or an order.")}</p><div className="rfq-reference"><span>{t("شناسه استعلام", "RFQ reference")}</span><code dir="ltr">{success.reference}</code><strong>{statusLabel(success.status, english)}</strong></div><div className="rfq-success-items">{success.items.map((item) => <div key={item.product.id}><b>{item.product.name}</b><span dir="ltr">{item.product.code} · {item.requested_quantity.toLocaleString(english ? "en-US" : "fa-IR")}</span></div>)}</div><div className="rfq-success-actions"><Link className="btn-primary" href={`/${locale}/shop`}>{t("ادامه خرید", "Continue shopping")}</Link><Link className="btn-secondary" href={`/${locale}/support`}>{t("امور مشتریان", "Customer Service")}</Link></div></section>;

  return <div className="rfq-form-shell">
    {contextLoading && <p className="rfq-context-note" role="status">{t("در حال دریافت اطلاعات محصول…", "Loading product context…")}</p>}
    {contextError && <p className="form-error" role="alert">{t("اطلاعات زمینه‌ای در دسترس نیست؛ می‌توانید استعلام عمومی ثبت کنید.", "The starting context is unavailable; you can still submit a general request.")}</p>}
    {contextWarning && <p className="rfq-context-note" role="status">{contextWarning}</p>}
    <form className="rfq-form" onSubmit={submit} aria-labelledby="rfq-form-title">
      <h2 id="rfq-form-title">{t("اطلاعات درخواست", "Request information")}</h2>
      <div className="rfq-fields"><label>{t("نام شرکت", "Company name")}<input value={form.company_name} onChange={(e) => setField("company_name", e.target.value)} autoComplete="organization" /></label><label>{t("نام تماس *", "Contact name *")}<input required value={form.contact_name} onChange={(e) => setField("contact_name", e.target.value)} autoComplete="name" /></label><label><span>{t("تلفن", "Phone")}{!form.email && " *"}</span><input dir="ltr" inputMode="tel" required={!form.email} value={form.phone} onChange={(e) => setField("phone", e.target.value)} autoComplete="tel" /></label><label><span>{t("ایمیل", "Email")}{!form.phone && " *"}</span><input dir="ltr" type="email" required={!form.phone} value={form.email} onChange={(e) => setField("email", e.target.value)} autoComplete="email" /></label><label>{t("روش تماس ترجیحی", "Preferred contact method")}<select value={form.preferred_contact_method} onChange={(e) => setField("preferred_contact_method", e.target.value)}><option value="">{t("انتخاب نشده", "Not specified")}</option><option value="phone">{t("تلفن", "Phone")}</option><option value="email">{t("ایمیل", "Email")}</option></select></label><label>{t("موضوع", "Subject")}<input value={form.subject} onChange={(e) => setField("subject", e.target.value)} /></label><label className="rfq-wide">{t("شرح نیاز", "Requirements")}<textarea value={form.message} onChange={(e) => setField("message", e.target.value)} placeholder={t("محصول، کاربرد یا نیاز فنی خود را توضیح دهید.", "Describe the product, application, or technical requirement.")} /></label></div>
      <section className="rfq-items" aria-labelledby="rfq-items-title"><header><div><span>{t("اقلام استعلام", "Quotation Request Items")}</span><h2 id="rfq-items-title">{t("محصولات مورد درخواست", "Requested products")}</h2></div><small>{lines.length.toLocaleString(english ? "en-US" : "fa-IR")} / ۲۵</small></header>{lines.length === 0 && <p className="rfq-empty-items">{t("در صورت نیاز، محصول را با جستجوی زیر اضافه کنید یا شرح نیاز خود را بنویسید.", "Add products using the search below, or describe your needs in the request.")}</p>}{lines.map((line) => <article className="rfq-item" key={line.product.id}><div className="rfq-item-heading"><div><b>{english ? line.product.name_en || line.product.name_fa : line.product.name_fa}</b><span dir="ltr">{line.product.sku || line.product.id}</span></div><button type="button" className="rfq-remove" aria-label={t(`حذف ${line.product.name_fa} از اقلام استعلام`, `Remove ${line.product.name_fa} from quotation request`)} onClick={() => { setLines((current) => current.filter((item) => item.product.id !== line.product.id)); requestAnimationFrame(() => addProductInput.current?.focus()); }}>{t("حذف قلم", "Remove item")}</button></div><div className="rfq-item-fields"><label>{t("تعداد درخواستی", "Requested quantity")}<input dir="ltr" type="number" min={1} max={1000000} value={line.quantity} aria-label={t(`تعداد درخواستی ${line.product.name_fa}`, `Requested quantity for ${line.product.name_fa}`)} onChange={(e) => updateLine(line.product.id, "quantity", e.target.value)} /></label><label>{t("یادداشت محصول", "Item note")}<input aria-label={t(`یادداشت ${line.product.name_fa}`, `Note for ${line.product.name_fa}`)} value={line.note} onChange={(e) => updateLine(line.product.id, "note", e.target.value)} /></label></div></article>)}<div className="rfq-add-product"><label htmlFor="rfq-product-search">{t("افزودن محصول دیگر", "Add another product")}</label><div><input ref={addProductInput} id="rfq-product-search" value={productQuery} onChange={(e) => setProductQuery(e.target.value)} placeholder={t("نام یا کد محصول", "Product name or code")} /><button type="button" className="btn-secondary" onClick={searchProducts} disabled={searchingProducts || productQuery.trim().length < 2 || lines.length >= 25}>{searchingProducts ? t("جستجو…", "Searching…") : lines.length >= 25 ? t("سقف اقلام تکمیل است", "Item limit reached") : t("جستجو", "Search")}</button></div><small className="rfq-search-hint">{t("برای جست و جو حداقل 2 حرف وارد کنید.", "Enter at least 2 characters to search.")}</small>{productResults.length > 0 && <ul className="rfq-product-results">{productResults.map((product) => <li key={product.id}><button type="button" onClick={() => addProduct(product)}><b>{english ? product.name_en || product.name_fa : product.name_fa}</b><span dir="ltr">{product.sku || product.id}</span></button></li>)}</ul>}{lines.length >= 25 && <small>{t("حداکثر ۲۵ قلم محصول مجاز است.", "A request can contain up to 25 products.")}</small>}</div></section>
      {error && <p className="form-error" role="alert">{error}</p>}<button className="btn-primary rfq-submit" type="submit" disabled={busy}>{busy ? t("در حال ارسال…", "Submitting…") : t("ثبت استعلام قیمت", "Submit request for quotation")}</button>
    </form>
  </div>;
}
