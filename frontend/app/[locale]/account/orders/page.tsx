"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { getOrders } from "../../../../lib/api/orders";
import { formatAccountDate, formatAccountNumber } from "../../../../lib/account-format";

type Order = { id: number; order_number: string; status_label: string; created_at: string; final_amount: string; items_count: number };

export default function OrdersPage() {
  const { locale = "fa" } = useParams<{ locale: string }>();
  const isEnglish = locale === "en";
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { getOrders<Order[]>().then(setOrders).catch((reason) => { setError(reason instanceof Error ? reason.message : "دریافت سفارش‌ها ناموفق بود."); setOrders([]); }); }, []);
  return <main className="site-container customer-orders-page">
    <header className="customer-orders-heading"><div><span>{isEnglish ? "Customer account" : "حساب کاربری"}</span><h1>{isEnglish ? "My orders" : "سفارش‌های من"}</h1></div><Link href={`/${locale}/account`}>{isEnglish ? "Back to account" : "بازگشت به حساب"}</Link></header>
    {orders === null ? <p className="account-empty orders-loading" role="status" aria-live="polite">{isEnglish ? "Loading orders…" : "در حال دریافت سفارش‌ها…"}</p> : error ? <section className="account-empty account-error-state" role="alert"><h2>{isEnglish ? "Orders could not be loaded" : "دریافت سفارش‌ها ناموفق بود"}</h2><p>{error}</p><button type="button" className="btn-primary" onClick={() => { setError(""); setOrders(null); getOrders<Order[]>().then(setOrders).catch((reason) => { setError(reason instanceof Error ? reason.message : "دریافت سفارش‌ها ناموفق بود."); setOrders([]); }); }}>{isEnglish ? "Try again" : "تلاش دوباره"}</button></section> : orders.length === 0 ? <section className="account-empty orders-empty-state" aria-labelledby="orders-empty-title"><span className="orders-empty-icon" aria-hidden="true">▣</span><h2 id="orders-empty-title">{isEnglish ? "No orders yet" : "سفارشی ثبت نشده است"}</h2><p className="orders-empty-description">{isEnglish ? "There are no orders in your account yet." : "هنوز سفارشی در حساب شما ثبت نشده است."}</p><Link className="btn-primary orders-empty-cta" href={`/${locale}/shop`}>{isEnglish ? "Go to shop" : "رفتن به فروشگاه"}</Link></section> : <div className="customer-order-grid">{orders.map(order => <Link className="customer-order-card" href={`/${locale}/account/orders/${order.id}`} key={order.id}><header><b dir="ltr">{order.order_number}</b><span className="order-status-badge"><i aria-hidden="true">●</i>{order.status_label}</span></header><p>{formatAccountDate(order.created_at, locale, true)}</p><footer><small>{formatAccountNumber(order.items_count, locale)} {isEnglish ? "items" : "کالا"}</small><strong>{formatAccountNumber(order.final_amount, locale)} {isEnglish ? "IRR" : "ریال"}</strong><span className="order-card-action">{isEnglish ? "View details" : "مشاهده جزئیات"} <b aria-hidden="true">←</b></span></footer></Link>)}</div>}
  </main>;
}
