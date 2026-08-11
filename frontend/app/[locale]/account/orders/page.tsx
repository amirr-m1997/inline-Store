"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type Order = { id:number; order_number:string; status_label:string; created_at:string; final_amount:string; items_count:number };
const money = (value:string) => Number(value).toLocaleString("fa-IR");

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[] | null>(null);
  useEffect(() => { fetch("/api/customer/orders/", { cache:"no-store" }).then(r => r.ok ? r.json() : []).then(setOrders).catch(() => setOrders([])); }, []);
  return <main className="site-container customer-orders-page">
    <header><div><span>حساب کاربری</span><h1>سفارش‌های من</h1></div><Link href="/fa/account">بازگشت به حساب</Link></header>
    {orders === null ? <p className="account-empty">در حال دریافت سفارش‌ها…</p> : orders.length === 0 ? <section className="account-empty"><p>هنوز سفارشی ثبت نکرده‌اید.</p><Link className="btn-primary" href="/fa/shop">رفتن به فروشگاه</Link></section> : <div className="customer-order-grid">{orders.map(order => <Link href={`/fa/account/orders/${order.id}`} key={order.id}><header><b dir="ltr">{order.order_number}</b><span>{order.status_label}</span></header><p>{new Intl.DateTimeFormat("fa-IR", { dateStyle:"long", timeStyle:"short" }).format(new Date(order.created_at))}</p><footer><small>{order.items_count.toLocaleString("fa-IR")} کالا</small><strong>{money(order.final_amount)} ریال</strong></footer></Link>)}</div>}
  </main>;
}
