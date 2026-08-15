"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { getPayment } from "../../../../../lib/api/payments";
import { paymentState, type PaymentState } from "../../../../../lib/payment-presenters";

export type PaymentResultData = { amount: string; reference_id?: string; status: string; verified_at: string | null; order: { order_number: string; status: string } };

const amount = (value: string) => `${Number(value).toLocaleString("fa-IR")} ریال`;

const stateCopy: Record<PaymentState, { title: string; description: string; icon: string }> = {
  success: { title: "پرداخت با موفقیت انجام شد", description: "پرداخت سفارش در سیستم ثبت شد.", icon: "✓" },
  failed: { title: "پرداخت ناموفق بود", description: "پرداخت تکمیل نشد. می‌توانید دوباره تلاش کنید.", icon: "!" },
  cancelled: { title: "پرداخت لغو شد", description: "پرداخت لغو شد و سفارش در انتظار پرداخت باقی ماند.", icon: "×" },
  pending: { title: "نتیجه پرداخت هنوز مشخص نیست", description: "وضعیت پرداخت در حال بررسی است. چند لحظه بعد دوباره بررسی کنید.", icon: "…" },
  unknown: { title: "وضعیت پرداخت نامشخص است", description: "نتیجه نهایی پرداخت از درگاه دریافت نشد.", icon: "?" },
};

export default function PaymentResultPage() {
  const { locale = "fa", paymentId } = useParams<{ locale: string; paymentId: string }>();
  const [payment, setPayment] = useState<PaymentResultData | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { getPayment<PaymentResultData>(paymentId).then(setPayment).catch((reason) => setError(reason instanceof Error ? reason.message : "نتیجه پرداخت دریافت نشد.")); }, [paymentId]);

  if (error) return <main className="payment-result-page site-container"><section className="payment-result-card" role="alert"><div className="payment-status-icon payment-status-icon--error" aria-hidden="true">!</div><h1>نتیجه پرداخت در دسترس نیست</h1><p>{error}</p><div className="payment-result-actions"><Link className="payment-button payment-button--primary" href={`/${locale}/cart`}>بازگشت به سبد خرید</Link><Link className="payment-button payment-button--secondary" href={`/${locale}`}>صفحه اصلی</Link></div></section></main>;
  if (!payment) return <main className="payment-result-page site-container"><section className="payment-result-card payment-loading" role="status" aria-live="polite"><span className="payment-spinner" aria-hidden="true" />در حال بررسی نتیجه پرداخت…</section></main>;

  const state = paymentState(payment.status); const copy = stateCopy[state]; const success = state === "success";
  return <main className="payment-result-page site-container"><section className={`payment-result-card payment-result-card--${state}`} role={state === "failed" || state === "cancelled" ? "alert" : "status"} aria-live="polite" aria-labelledby="payment-result-title" aria-describedby="payment-result-description">
    <div className="payment-status-icon" aria-hidden="true">{copy.icon}</div><p className="payment-eyebrow">نتیجه پرداخت</p><h1 id="payment-result-title">{copy.title}</h1><p id="payment-result-description">{copy.description}</p>
    <dl className="payment-result-details"><div><dt>شماره سفارش</dt><dd dir="ltr">{payment.order.order_number}</dd></div><div><dt>مبلغ</dt><dd>{amount(payment.amount)}</dd></div>{payment.reference_id && <div><dt>شماره پیگیری پرداخت</dt><dd dir="ltr">{payment.reference_id}</dd></div>}</dl>
    <div className="payment-result-actions">
      {success ? <><Link className="payment-button payment-button--primary" href={`/${locale}/account/orders`}>مشاهده سفارش‌ها</Link><Link className="payment-button payment-button--secondary" href={`/${locale}/shop`}>ادامه خرید</Link></> : state === "pending" || state === "unknown" ? <><Link className="payment-button payment-button--primary" href={`/${locale}/payment/${paymentId}`}>بازگشت به پرداخت</Link><Link className="payment-button payment-button--secondary" href={`/${locale}/account/orders`}>مشاهده سفارش‌ها</Link></> : <><Link className="payment-button payment-button--primary" href={`/${locale}/payment/${paymentId}`}>تلاش دوباره برای پرداخت</Link><Link className="payment-button payment-button--secondary" href={`/${locale}/cart`}>بازگشت به سبد خرید</Link></>}
    </div>
  </section></main>;
}
