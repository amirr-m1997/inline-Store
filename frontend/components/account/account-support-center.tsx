"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import type { Customer } from "../../services/auth-client";
import { getProfile } from "../../lib/api/account";
import { getSupportRequests, getWarrantyRegistrations } from "../../lib/api/content";
import { formatAccountDate } from "../../lib/account-format";

type SupportRecord = { reference: string; request_type: string; status: string; subject?: string; submitted_at: string; product?: number | null; order?: number | null };
type WarrantyRecord = { reference: string; status: string; submitted_at: string; serial_number?: string; product?: number | null; order?: number | null };

const requestTypes: Record<string, [string, string]> = {
  complaint: ["شکایت", "Complaint"], product_support: ["پشتیبانی محصول", "Product support"], order_support: ["پشتیبانی سفارش", "Order support"], warranty: ["گارانتی", "Warranty"], sales: ["فروش", "Sales"], other: ["سایر", "Other"],
};
const statuses: Record<string, [string, string]> = { submitted: ["ثبت‌شده", "Submitted"], under_review: ["در حال بررسی", "Under review"], resolved: ["رسیدگی‌شده", "Resolved"], closed: ["بسته‌شده", "Closed"] };

export function AccountSupportCenter() {
  const { locale = "fa" } = useParams<{ locale: string }>();
  const router = useRouter();
  const english = locale === "en";
  const t = (fa: string, en: string) => english ? en : fa;
  const [requests, setRequests] = useState<SupportRecord[] | null>(null);
  const [warranties, setWarranties] = useState<WarrantyRecord[] | null>(null);
  const [requestError, setRequestError] = useState(false);
  const [warrantyError, setWarrantyError] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true); setRequestError(false); setWarrantyError(false); setRequests(null); setWarranties(null);
    try { await getProfile<Customer>(); } catch { router.replace(`/${locale}/login`); return; }
    await Promise.all([
      getSupportRequests<SupportRecord>().then(setRequests).catch(() => setRequestError(true)),
      getWarrantyRegistrations<WarrantyRecord>().then(setWarranties).catch(() => setWarrantyError(true)),
    ]);
    setLoading(false);
  }, [locale, router]);
  useEffect(() => { void load(); }, [load]);

  const status = (value: string) => statuses[value] ? t(...statuses[value]) : value;
  const type = (value: string) => requestTypes[value] ? t(...requestTypes[value]) : value;
  const context = (product?: number | null, order?: number | null) => [product != null && `${t("محصول", "Product")} #${product}`, order != null && `${t("سفارش", "Order")} #${order}`].filter(Boolean).join(" · ");

  if (loading) return <main className="account-support-page site-container"><p role="status" aria-live="polite">{t("در حال دریافت سوابق پشتیبانی…", "Loading your support history…")}</p></main>;
  return <main className="account-support-page site-container">
    <header className="account-support-heading"><div><span>{t("مرکز پشتیبانی حساب", "Account support center")}</span><h1>{t("پشتیبانی", "Support")}</h1><p>{t("درخواست‌های پشتیبانی و ثبت‌های گارانتی حساب خود را در این بخش پیگیری کنید.", "Review your support requests and warranty registration requests in one place.")}</p></div><Link className="btn-secondary" href={`/${locale}/support`}>{t("مرکز خدمات مشتریان", "Support hub")}</Link></header>
    {(requestError || warrantyError) && <div className="account-message error" role="alert"><p>{t("دریافت بخشی از سوابق پشتیبانی ناموفق بود.", "Some support history could not be loaded.")}</p><button type="button" onClick={() => void load()}>{t("تلاش دوباره", "Try again")}</button></div>}
    <section className="account-support-section" aria-labelledby="support-requests-title"><header><div><span>{t("پیگیری درخواست‌ها", "Request tracking")}</span><h2 id="support-requests-title">{t("درخواست‌های پشتیبانی", "Support requests")}</h2></div><Link className="btn-primary" href={`/${locale}/support/request`}>{t("ثبت درخواست", "Submit request")}</Link></header>{requestError ? <p className="account-empty" role="alert">{t("سوابق درخواست‌ها در دسترس نیست.", "Support request history is unavailable.")}</p> : requests?.length ? <div className="account-support-list">{requests.map((item) => <article key={item.reference} className="account-support-record"><div className="account-support-record-top"><code dir="ltr">{item.reference}</code><span className="account-status">{status(item.status)}</span></div><h3>{item.subject || t("بدون موضوع", "No subject")}</h3><p>{type(item.request_type)}{context(item.product, item.order) && ` · ${context(item.product, item.order)}`}</p><time dateTime={item.submitted_at}>{formatAccountDate(item.submitted_at, locale, true)}</time></article>)}</div> : <div className="account-empty account-support-empty"><p>{t("هنوز درخواست پشتیبانی ثبت نکرده‌اید.", "You have not submitted a support request yet.")}</p><Link href={`/${locale}/support/request`}>{t("ثبت درخواست پشتیبانی", "Submit a support request")}</Link></div>}</section>
    <section className="account-support-section" aria-labelledby="warranty-history-title"><header><div><span>{t("ثبت و پیگیری", "Registration tracking")}</span><h2 id="warranty-history-title">{t("درخواست‌های ثبت گارانتی", "Warranty registration requests")}</h2></div><Link className="btn-secondary" href={`/${locale}/support/warranty`}>{t("ثبت درخواست گارانتی", "Register warranty request")}</Link></header>{warrantyError ? <p className="account-empty" role="alert">{t("سوابق ثبت گارانتی در دسترس نیست.", "Warranty history is unavailable.")}</p> : warranties?.length ? <div className="account-support-list">{warranties.map((item) => <article key={item.reference} className="account-support-record"><div className="account-support-record-top"><code dir="ltr">{item.reference}</code><span className="account-status">{status(item.status)}</span></div><h3>{t("درخواست ثبت گارانتی", "Warranty registration request")}</h3><p>{item.serial_number ? `${t("شناسه محصول", "Product identifier")}: ` : ""}<bdi dir="ltr">{item.serial_number || t("ثبت نشده", "Not provided")}</bdi>{context(item.product, item.order) && ` · ${context(item.product, item.order)}`}</p><time dateTime={item.submitted_at}>{formatAccountDate(item.submitted_at, locale, true)}</time></article>)}</div> : <div className="account-empty account-support-empty"><p>{t("هنوز درخواست ثبت گارانتی ندارید.", "You have not submitted a warranty registration request yet.")}</p><Link href={`/${locale}/support/warranty`}>{t("ثبت درخواست گارانتی", "Register warranty request")}</Link></div>}</section>
  </main>;
}
