"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { completeMockPayment, getPayment } from "../../../../lib/api/payments";
import { paymentGatewayLabel } from "../../../../lib/payment-presenters";

export type PaymentData = { id: number; amount: string; status: string; gateway?: string; order: { order_number: string } };

const amount = (value: string) => `${Number(value).toLocaleString("fa-IR")} ریال`;

export default function MockPaymentPage() {
  const { locale = "fa", paymentId } = useParams<{ locale: string; paymentId: string }>();
  const router = useRouter();
  const [payment, setPayment] = useState<PaymentData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getPayment<PaymentData>(paymentId).then(setPayment).catch((reason) => setError(reason instanceof Error ? reason.message : "پرداخت یافت نشد."));
  }, [paymentId]);

  const finish = async (outcome: "success" | "cancelled") => {
    setLoading(true); setError("");
    try { await completeMockPayment(paymentId, outcome); router.replace(`/${locale}/payment/result/${paymentId}`); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "پردازش پرداخت ناموفق بود."); }
    finally { setLoading(false); }
  };

  if (error && !payment) return <main className="payment-shell" dir="rtl"><section className="payment-card payment-error-card" role="alert"><div className="payment-status-icon payment-status-icon--error" aria-hidden="true">!</div><h1>ورود به پرداخت ممکن نیست</h1><p>{error}</p><button type="button" className="payment-button payment-button--secondary" onClick={() => router.back()}>بازگشت</button></section></main>;
  if (!payment) return <main className="payment-shell" dir="rtl"><section className="payment-card payment-loading" role="status" aria-live="polite"><span className="payment-spinner" aria-hidden="true" />در حال دریافت اطلاعات پرداخت…</section></main>;

  const gateway = paymentGatewayLabel(payment.gateway);
  return <main className="payment-shell" dir="rtl">
    <section className="payment-card" aria-labelledby="payment-title">
      <header className="payment-card-header">
        <div><span className="payment-brand-mark" aria-hidden="true">پ</span><div><p className="payment-eyebrow">پرداخت سفارش</p><h1 id="payment-title">{gateway}</h1></div></div>
        <span className="payment-environment">محیط آزمایشی</span>
      </header>
      <div className="payment-context" aria-label="اطلاعات سفارش و پرداخت">
        <div><small>شماره سفارش</small><b dir="ltr">{payment.order.order_number}</b></div>
        <div><small>شناسه پرداخت</small><b dir="ltr">{payment.id}</b></div>
        <div className="payment-amount"><small>مبلغ قابل پرداخت</small><strong>{amount(payment.amount)}</strong></div>
      </div>
      <p className="payment-next-step">اطلاعات پرداخت آزمایشی را وارد کنید و سپس گزینهٔ پرداخت را انتخاب کنید.</p>
      <form onSubmit={(event) => { event.preventDefault(); void finish("success"); }}>
        <label htmlFor="payment-card-number">شماره کارت<input id="payment-card-number" dir="ltr" inputMode="numeric" defaultValue="6037997512345678" maxLength={16} required /></label>
        <div className="payment-form-row"><label htmlFor="payment-cvv">CVV2<input id="payment-cvv" dir="ltr" inputMode="numeric" defaultValue="123" required /></label><label htmlFor="payment-expiry-month">تاریخ انقضا<span><input id="payment-expiry-month" aria-label="ماه انقضا" dir="ltr" inputMode="numeric" defaultValue="08" maxLength={2} required /><input aria-label="سال انقضا" dir="ltr" inputMode="numeric" defaultValue="09" maxLength={2} required /></span></label></div>
        <label htmlFor="payment-otp">رمز پویا<input id="payment-otp" dir="ltr" inputMode="numeric" defaultValue="123456" required /></label>
        {error && <p className="payment-form-error" role="alert" aria-live="assertive">{error}</p>}
        <button className="payment-button payment-button--primary" disabled={loading}>{loading ? "در حال پردازش…" : `پرداخت ${amount(payment.amount)}`}</button>
        <button type="button" className="payment-button payment-button--secondary" disabled={loading} onClick={() => void finish("cancelled")}>انصراف و بازگشت به فروشگاه</button>
      </form>
      <footer className="payment-disclosure">این صفحه شبیه‌ساز محلی است؛ اطلاعات کارت واقعی دریافت یا ذخیره نمی‌شود.</footer>
    </section>
  </main>;
}
