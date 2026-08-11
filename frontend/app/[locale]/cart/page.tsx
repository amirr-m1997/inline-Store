"use client";

import Link from "next/link";
import Image from "next/image";
import { useCallback, useEffect, useState } from "react";

type Customer = {
  customer_first_name: string; customer_last_name: string; customer_email: string; customer_phone: string;
  customer_company_name: string; customer_national_id: string; shipping_province: string; shipping_city: string;
  shipping_postal_code: string; shipping_address: string;
};
type CartItem = { id: number; quantity: number; line_total: string | null; product: { name: string; slug: string; unit: string; available_quantity: number | null; images: { image: string; alt_text: string; is_primary: boolean }[]; price: { final_amount: string } | null } };
type Cart = { id: number; guest_token: string | null; items: CartItem[]; subtotal: string; discount_amount: string; total: string; discount: { code: string; percentage: string } | null; customer: Customer; customer_complete: boolean };

const emptyCustomer: Customer = { customer_first_name: "", customer_last_name: "", customer_email: "", customer_phone: "", customer_company_name: "", customer_national_id: "", shipping_province: "", shipping_city: "", shipping_postal_code: "", shipping_address: "" };

function requestHeaders(json = false) {
  const headers: Record<string, string> = {};
  const guestToken = localStorage.getItem("guestCartToken");
  if (guestToken) headers["X-Guest-Token"] = guestToken;
  if (json) headers["Content-Type"] = "application/json";
  return headers;
}

export default function CartPage() {
  const [cart, setCart] = useState<Cart | null>(null);
  const [customer, setCustomer] = useState<Customer>(emptyCustomer);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [orderReference, setOrderReference] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [discountCode, setDiscountCode] = useState("");
  const [applyingDiscount, setApplyingDiscount] = useState(false);

  const acceptCart = useCallback((data: Cart) => {
    setCart(data); setCustomer(data.customer ?? emptyCustomer);
    if (data.guest_token) localStorage.setItem("guestCartToken", data.guest_token);
  }, []);
  const load = useCallback(async () => {
    setError("");
    try {
      const response = await fetch("/api/v1/cart/", { headers: requestHeaders(), cache: "no-store" });
      if (!response.ok) throw new Error("دریافت سبد خرید ناموفق بود.");
      acceptCart(await response.json());
    } catch (reason) { setError(reason instanceof Error ? reason.message : "خطایی رخ داد."); }
    finally { setLoading(false); }
  }, [acceptCart]);
  useEffect(() => { void load(); }, [load]);

  const changeQuantity = async (item: CartItem, quantity: number) => {
    setError("");
    const response = await fetch(`/api/v1/cart/items/${item.id}/`, { method: quantity < 1 ? "DELETE" : "PATCH", headers: requestHeaders(quantity > 0), body: quantity > 0 ? JSON.stringify({ quantity }) : undefined });
    if (!response.ok) { const data = await response.json().catch(() => ({})); setError(data.detail || "تغییر تعداد ناموفق بود."); return; }
    if (response.status === 204) await load(); else acceptCart(await response.json());
  };
  const saveCustomerData = async () => {
    setMessage(""); setError("");
    try {
      const response = await fetch("/api/v1/cart/", { method: "PATCH", headers: requestHeaders(true), body: JSON.stringify({ customer, save_to_profile: true }) });
      const data = await response.json();
      if (!response.ok) throw new Error(Object.values(data).flat().join(" ") || "ذخیره اطلاعات مشتری ناموفق بود.");
      acceptCart(data); return data as Cart;
    } catch (reason) { setError(reason instanceof Error ? reason.message : "خطایی رخ داد."); return null; }
  };
  const saveCustomer = async (event: React.FormEvent) => {
    event.preventDefault(); setSaving(true);
    const saved = await saveCustomerData();
    if (saved) setMessage("اطلاعات مشتری و نشانی تحویل ذخیره شد.");
    setSaving(false);
  };
  const submitOrder = async () => {
    if (!cart?.items.length || submitting) return;
    setSubmitting(true); setMessage(""); setError("");
    const saved = await saveCustomerData();
    if (!saved?.customer_complete) { setError("لطفاً تمام فیلدهای الزامی اطلاعات مشتری را کامل کنید."); setSubmitting(false); return; }
    const response = await fetch("/api/v1/cart/checkout/", { method: "POST", headers: requestHeaders(true) });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) setError(data.detail || "ثبت سفارش ناموفق بود.");
    else if (data.payment_url) { window.location.assign(data.payment_url); }
    setSubmitting(false);
  };
  const field = (name: keyof Customer, value: string) => setCustomer((current) => ({ ...current, [name]: value }));
  const applyDiscount = async (event: React.FormEvent) => { event.preventDefault(); setApplyingDiscount(true); setError(""); setMessage(""); const response = await fetch("/api/v1/cart/discount/", { method: "POST", headers: requestHeaders(true), body: JSON.stringify({ code: discountCode }) }); const data = await response.json().catch(() => ({})); setApplyingDiscount(false); if (!response.ok) return setError(data.detail || "اعمال کد تخفیف ناموفق بود."); acceptCart(data); setDiscountCode(""); setMessage("کد تخفیف با موفقیت اعمال شد."); };
  const removeDiscount = async () => { const response = await fetch("/api/v1/cart/discount/", { method: "DELETE", headers: requestHeaders(true) }); if (response.ok) { acceptCart(await response.json()); setMessage("کد تخفیف حذف شد."); } };
  const localCustomerComplete = Boolean(customer.customer_first_name && customer.customer_last_name && customer.customer_phone && customer.shipping_province && customer.shipping_city && customer.shipping_postal_code && customer.shipping_address);

  if (loading) return <main className="container-page py-10">در حال دریافت سبد…</main>;
  if (error && !cart) return <main className="container-page py-10"><p className="text-red-700">{error}</p><button className="btn-primary mt-4" onClick={() => { setLoading(true); void load(); }}>تلاش دوباره</button></main>;
  if (!cart) return null;
  if (orderReference) return <main className="container-page py-12"><section className="card mx-auto max-w-xl text-center"><div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-emerald-100 text-3xl text-emerald-700">✓</div><h1 className="mt-5 text-2xl font-black">سفارش با موفقیت ثبت شد</h1><p className="mt-3 text-sm text-slate-500">شماره پیگیری سفارش</p><b className="mt-2 block text-xl text-emerald-700" dir="ltr">{orderReference}</b><p className="mt-5 text-sm leading-7 text-slate-600">موجودی کالاهای سفارش برای ۲۴ ساعت رزرو شد. کارشناسان فروش برای ادامه فرایند با شما تماس خواهند گرفت.</p><Link className="btn-primary mt-5 inline-block no-underline" href="/fa">بازگشت به فروشگاه</Link></section></main>;

  return <main className="cart-page container-page py-8">
    <h1 className="mb-6 text-2xl font-black">سبد خرید و اطلاعات مشتری</h1>
    {error && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
      <section className="card">
        <h2 className="text-lg font-black">کالاهای انتخاب‌شده</h2>
        {!cart.items.length && <div className="py-12 text-center"><p className="text-slate-500">سبد خرید شما خالی است.</p><Link className="btn-primary mt-4 inline-block no-underline" href="/fa/categories">مشاهده محصولات</Link></div>}
        {cart.items.map((item) => { const productImage = item.product.images?.find((image) => image.is_primary) ?? item.product.images?.[0]; return <article className="cart-item mt-4 grid gap-3 border-b pb-4 sm:grid-cols-[1fr_auto] sm:items-center" key={item.id}>
          <div className="cart-item-info">{productImage && <Link className="cart-item-image" href={`/fa/product/${item.product.slug}`}><Image src={productImage.image} alt={productImage.alt_text || item.product.name} fill sizes="72px" /></Link>}<div><Link className="font-bold text-slate-800 no-underline" href={`/fa/product/${item.product.slug}`}>{item.product.name}</Link><p className="mt-1 text-xs text-slate-500">قیمت واحد: {item.product.price ? Number(item.product.price.final_amount).toLocaleString("fa-IR") : "ثبت نشده"} ریال</p><p className="mt-1 text-sm font-bold">جمع: {item.line_total ? Number(item.line_total).toLocaleString("fa-IR") : "—"} ریال</p></div></div>
          <div className="flex items-center gap-2"><button className="h-9 w-9 rounded border" onClick={() => void changeQuantity(item, item.quantity - 1)}>−</button><b className="min-w-8 text-center">{item.quantity.toLocaleString("fa-IR")}</b><button className="h-9 w-9 rounded border" disabled={item.product.available_quantity !== null && item.quantity >= item.product.available_quantity} onClick={() => void changeQuantity(item, item.quantity + 1)}>+</button><button className="mr-2 rounded border border-red-200 px-3 py-2 text-xs text-red-700" onClick={() => void changeQuantity(item, 0)}>حذف</button></div>
        </article>; })}
        <div className="cart-discount-box"><h3>کد تخفیف</h3>{cart.discount ? <div className="cart-applied-discount"><div><b dir="ltr">{cart.discount.code}</b><span>٪{Number(cart.discount.percentage).toLocaleString("fa-IR")} تخفیف اعمال شد</span></div><button type="button" onClick={() => void removeDiscount()}>حذف</button></div> : <form onSubmit={applyDiscount}><input dir="ltr" value={discountCode} onChange={(event) => setDiscountCode(event.target.value)} placeholder="کد تخفیف را وارد کنید" required /><button disabled={applyingDiscount}>{applyingDiscount ? "در حال بررسی…" : "اعمال کد"}</button></form>}</div>
        <dl className="cart-totals"><div><dt>جمع کالاها</dt><dd>{Number(cart.subtotal).toLocaleString("fa-IR")} ریال</dd></div>{Number(cart.discount_amount) > 0 && <div className="discount-row"><dt>تخفیف</dt><dd>− {Number(cart.discount_amount).toLocaleString("fa-IR")} ریال</dd></div>}<div className="grand-total"><dt>مبلغ قابل پرداخت</dt><dd>{Number(cart.total).toLocaleString("fa-IR")} ریال</dd></div></dl>
      </section>

      <form className="card h-max" onSubmit={saveCustomer}>
        <h2 className="text-lg font-black">اطلاعات مشتری و تحویل</h2><p className="mt-2 text-xs leading-6 text-slate-500">فیلدهای ستاره‌دار برای ادامه سفارش الزامی هستند.</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
          <label className="text-xs">نام *<input className="input mt-1" value={customer.customer_first_name} onChange={(e) => field("customer_first_name", e.target.value)} required /></label>
          <label className="text-xs">نام خانوادگی *<input className="input mt-1" value={customer.customer_last_name} onChange={(e) => field("customer_last_name", e.target.value)} required /></label>
          <label className="text-xs">شماره تماس *<input className="input mt-1" dir="ltr" value={customer.customer_phone} onChange={(e) => field("customer_phone", e.target.value)} required /></label>
          <label className="text-xs">ایمیل<input className="input mt-1" type="email" dir="ltr" value={customer.customer_email} onChange={(e) => field("customer_email", e.target.value)} /></label>
          <label className="text-xs">نام شرکت<input className="input mt-1" value={customer.customer_company_name} onChange={(e) => field("customer_company_name", e.target.value)} /></label>
          <label className="text-xs">شناسه ملی/کد ملی<input className="input mt-1" dir="ltr" value={customer.customer_national_id} onChange={(e) => field("customer_national_id", e.target.value)} /></label>
          <label className="text-xs">استان *<input className="input mt-1" value={customer.shipping_province} onChange={(e) => field("shipping_province", e.target.value)} required /></label>
          <label className="text-xs">شهر *<input className="input mt-1" value={customer.shipping_city} onChange={(e) => field("shipping_city", e.target.value)} required /></label>
          <label className="text-xs sm:col-span-2 lg:col-span-1 xl:col-span-2">کد پستی *<input className="input mt-1" dir="ltr" inputMode="numeric" maxLength={10} value={customer.shipping_postal_code} onChange={(e) => field("shipping_postal_code", e.target.value)} required /></label>
          <label className="text-xs sm:col-span-2 lg:col-span-1 xl:col-span-2">نشانی کامل *<textarea className="input mt-1 min-h-24" value={customer.shipping_address} onChange={(e) => field("shipping_address", e.target.value)} required /></label>
        </div>
        <button className="btn-primary mt-5 w-full" disabled={saving}>{saving ? "در حال ذخیره…" : "ذخیره اطلاعات مشتری"}</button>
        {message && <p className="mt-3 text-sm text-emerald-700">{message}</p>}
        <button type="button" onClick={() => void submitOrder()} className="mt-3 w-full rounded-lg border px-4 py-2 text-sm font-bold disabled:opacity-50" disabled={!cart.items.length || !localCustomerComplete || saving || submitting}>{submitting ? "در حال ثبت سفارش…" : "ادامه و ثبت سفارش"}</button>
      </form>
    </div>
  </main>;
}
