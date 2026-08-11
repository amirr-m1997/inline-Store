"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

type PaymentData = { amount: string; reference_id: string; status: string; verified_at: string | null; order: { order_number: string; status: string } };
function requestHeaders(): Record<string, string> { const token = localStorage.getItem("guestCartToken"); return token ? { "X-Guest-Token": token } : {}; }

export default function PaymentResultPage() {
  const { locale = "fa", paymentId } = useParams<{ locale: string; paymentId: string }>(); const [payment, setPayment] = useState<PaymentData | null>(null);
  useEffect(() => { fetch(`/api/v1/orders/payments/${paymentId}/`, { headers: requestHeaders(), cache: "no-store" }).then((response) => response.ok ? response.json() : null).then(setPayment); }, [paymentId]);
  if (!payment) return <main className="payment-result-page site-container">در حال بررسی نتیجه پرداخت…</main>;
  const success = payment.status === "verified";
  return <main className="payment-result-page site-container"><section className={success ? "success" : "failed"}><i>{success ? "✓" : "×"}</i><h1>{success ? "پرداخت با موفقیت انجام شد" : payment.status === "cancelled" ? "پرداخت لغو شد" : "پرداخت ناموفق بود"}</h1>{success ? <><p>سفارش شما پرداخت و در سیستم ثبت شد.</p><dl><div><dt>شماره سفارش</dt><dd dir="ltr">{payment.order.order_number}</dd></div><div><dt>شماره پیگیری پرداخت</dt><dd dir="ltr">{payment.reference_id}</dd></div><div><dt>مبلغ پرداخت‌شده</dt><dd>{Number(payment.amount).toLocaleString("fa-IR")} ریال</dd></div></dl><div><Link className="btn-primary" href={`/${locale}/account`}>مشاهده سفارش‌ها</Link><Link href={`/${locale}/shop`}>ادامه خرید</Link></div></> : <><p>وجهی از حساب شما کسر نشده است. می‌توانید دوباره پرداخت را امتحان کنید.</p><div><Link className="btn-primary" href={`/${locale}/payment/${paymentId}`}>تلاش مجدد برای پرداخت</Link><Link href={`/${locale}`}>صفحه اصلی</Link></div></>}</section></main>;
}
