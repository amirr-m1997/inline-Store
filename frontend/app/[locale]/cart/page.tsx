"use client";

import Link from "next/link";
import Image from "next/image";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ApiError } from "../../../lib/api/client";
import { getCart, removeItem, updateItem } from "../../../lib/api/cart";
import { initializeCheckout, saveCheckoutCustomer } from "../../../lib/api/checkout";
import { applyDiscount, removeDiscount } from "../../../lib/api/discounts";
import { CheckoutProgress } from "../../../components/cart/checkout-progress";
import { CartSummary } from "../../../components/cart/cart-summary";

type Customer = {
  customer_first_name: string; customer_last_name: string; customer_email: string; customer_phone: string;
  customer_company_name: string; customer_national_id: string; shipping_province: string; shipping_city: string;
  shipping_postal_code: string; shipping_address: string;
};
type CartItem = { id: number; quantity: number; line_total: string | null; product: { name: string; code?: string; slug: string; unit: string; available_quantity: number | null; images: { image: string; alt_text: string; is_primary: boolean }[]; price: { final_amount: string } | null } };
type Cart = { id: number; guest_token: string | null; items: CartItem[]; subtotal: string; discount_amount: string; total: string; discount: { code: string; percentage: string } | null; customer: Customer; customer_complete: boolean };

const emptyCustomer: Customer = { customer_first_name: "", customer_last_name: "", customer_email: "", customer_phone: "", customer_company_name: "", customer_national_id: "", shipping_province: "", shipping_city: "", shipping_postal_code: "", shipping_address: "" };

const money = (value: string | null | undefined) => value == null ? "—" : `${Number(value).toLocaleString("fa-IR")} ریال`;

export default function CartPage() {
  const { locale = "fa" } = useParams<{ locale: string }>();
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
  const [updatingItem, setUpdatingItem] = useState<number | null>(null);

  const acceptCart = useCallback((data: Cart) => {
    setCart(data); setCustomer(data.customer ?? emptyCustomer);
    if (data.guest_token) localStorage.setItem("guestCartToken", data.guest_token);
  }, []);
  const load = useCallback(async () => {
    setError("");
    try {
      acceptCart(await getCart<Cart>());
    } catch (reason) { setError(reason instanceof Error ? reason.message : "خطایی رخ داد."); }
    finally { setLoading(false); }
  }, [acceptCart]);
  useEffect(() => { void load(); }, [load]);

  const changeQuantity = async (item: CartItem, quantity: number) => {
    if (updatingItem === item.id) return;
    setUpdatingItem(item.id);
    setError("");
    try { if (quantity < 1) { await removeItem(item.id); await load(); } else acceptCart(await updateItem(item.id, quantity) as Cart); } catch (reason) { setError(reason instanceof Error ? reason.message : "تغییر تعداد ناموفق بود."); } finally { setUpdatingItem(null); }
  };
  const saveCustomerData = async () => {
    setMessage(""); setError("");
    try {
      const data = await saveCheckoutCustomer<Cart>(customer);
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
    try { const data = await initializeCheckout<{ payment_url?: string }>(); if (data.payment_url) window.location.assign(data.payment_url); } catch (reason) { setError(reason instanceof ApiError ? reason.message : "ثبت سفارش ناموفق بود."); }
    setSubmitting(false);
  };
  const field = (name: keyof Customer, value: string) => setCustomer((current) => ({ ...current, [name]: value }));
  const applyDiscountCode = async (event: React.FormEvent) => { event.preventDefault(); setApplyingDiscount(true); setError(""); setMessage(""); try { acceptCart(await applyDiscount<Cart>(discountCode)); setDiscountCode(""); setMessage("کد تخفیف با موفقیت اعمال شد."); } catch (reason) { setError(reason instanceof Error ? reason.message : "اعمال کد تخفیف ناموفق بود."); } finally { setApplyingDiscount(false); } };
  const removeDiscountCode = async () => { setError(""); try { acceptCart(await removeDiscount<Cart>()); setMessage("کد تخفیف حذف شد."); } catch (reason) { setError(reason instanceof Error ? reason.message : "حذف کد تخفیف ناموفق بود."); } };
  const localCustomerComplete = Boolean(customer.customer_first_name && customer.customer_last_name && customer.customer_phone && customer.shipping_province && customer.shipping_city && customer.shipping_postal_code && customer.shipping_address);

  if (loading) return <main className="container-page py-10" role="status" aria-live="polite">در حال دریافت سبد…</main>;
  if (error && !cart) return <main className="container-page py-10"><p className="text-red-700" role="alert">{error}</p><button className="btn-primary mt-4" onClick={() => { setLoading(true); void load(); }}>تلاش دوباره</button></main>;
  if (!cart) return null;
  if (orderReference) return <main className="container-page py-12"><section className="card mx-auto max-w-xl text-center"><div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-emerald-100 text-3xl text-emerald-700">✓</div><h1 className="mt-5 text-2xl font-black">سفارش با موفقیت ثبت شد</h1><p className="mt-3 text-sm text-slate-500">شماره پیگیری سفارش</p><b className="mt-2 block text-xl text-emerald-700" dir="ltr">{orderReference}</b><p className="mt-5 text-sm leading-7 text-slate-600">موجودی کالاهای سفارش برای ۲۴ ساعت رزرو شد. کارشناسان فروش برای ادامه فرایند با شما تماس خواهند گرفت.</p><Link className="btn-primary mt-5 inline-block no-underline" href={`/${locale}`}>بازگشت به فروشگاه</Link></section></main>;

  return <main className="cart-page container-page py-8">
    <h1 className="mb-4 text-2xl font-black">سبد خرید و ثبت سفارش</h1>
    <CheckoutProgress hasItems={cart.items.length > 0} customerComplete={localCustomerComplete} />
    {error && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700" role="alert" aria-live="assertive">{error}</p>}
    <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
      <section className="card">
        <h2 className="text-lg font-black">کالاهای انتخاب‌شده <span className="cart-item-count">({cart.items.length.toLocaleString("fa-IR")} کالا)</span></h2>
        {!cart.items.length && <div className="py-12 text-center"><p className="text-slate-500">سبد خرید شما خالی است.</p><Link className="btn-primary mt-4 inline-block no-underline" href={`/${locale}/categories`}>مشاهده محصولات</Link></div>}
        {cart.items.map((item) => { const productImage = item.product.images?.find((image) => image.is_primary) ?? item.product.images?.[0]; return <article className="cart-item mt-4 grid gap-3 border-b pb-4 sm:grid-cols-[1fr_auto] sm:items-center" key={item.id}>
          <div className="cart-item-info">{productImage && <Link className="cart-item-image" href={`/${locale}/product/${item.product.slug}`}><Image src={productImage.image} alt={productImage.alt_text || item.product.name} fill sizes="72px" /></Link>}<div><Link className="font-bold text-slate-800 no-underline" href={`/${locale}/product/${item.product.slug}`}>{item.product.name}</Link>{item.product.code && <p className="mt-1 text-xs text-slate-500">کد کالا: <b dir="ltr">{item.product.code}</b></p>}<p className="mt-1 text-xs text-slate-500">قیمت واحد: {money(item.product.price?.final_amount)}</p><p className="mt-1 text-sm font-bold">جمع: {money(item.line_total)}</p></div></div>
          <div className="cart-item-controls" aria-label={`کنترل‌های ${item.product.name}`} aria-busy={updatingItem === item.id}><button type="button" className="h-9 w-9 rounded border" disabled={updatingItem === item.id} onClick={() => void changeQuantity(item, item.quantity - 1)} aria-label={`کاهش تعداد ${item.product.name}`}>−</button><b className="min-w-8 text-center" aria-live="polite">{updatingItem === item.id ? "…" : item.quantity.toLocaleString("fa-IR")}</b><button type="button" className="h-9 w-9 rounded border" disabled={updatingItem === item.id || (item.product.available_quantity !== null && item.quantity >= item.product.available_quantity)} onClick={() => void changeQuantity(item, item.quantity + 1)} aria-label={`افزایش تعداد ${item.product.name}`}>+</button><button type="button" className="mr-2 rounded border border-red-200 px-3 py-2 text-xs text-red-700" disabled={updatingItem === item.id} onClick={() => void changeQuantity(item, 0)} aria-label={`حذف ${item.product.name} از سبد`}>حذف</button></div>
        </article>; })}
        <details className="cart-discount-box"><summary>کد تخفیف <small>اختیاری</small></summary>{cart.discount ? <div className="cart-applied-discount"><div><b dir="ltr">{cart.discount.code}</b><span role="status">٪{Number(cart.discount.percentage).toLocaleString("fa-IR")} تخفیف اعمال شد</span></div><button type="button" onClick={() => void removeDiscountCode()} aria-label={`حذف کد تخفیف ${cart.discount.code}`}>حذف</button></div> : <form onSubmit={applyDiscountCode}><label htmlFor="discount-code" className="sr-only">کد تخفیف</label><input id="discount-code" dir="ltr" value={discountCode} onChange={(event) => setDiscountCode(event.target.value)} placeholder="کد تخفیف را وارد کنید" required /><button disabled={applyingDiscount}>{applyingDiscount ? "در حال بررسی…" : "اعمال کد"}</button></form>}</details>
        <CartSummary cart={cart} />
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
        {message && <p className="mt-3 text-sm text-emerald-700" role="status" aria-live="polite">{message}</p>}
        <p id="checkout-next-action" className="checkout-next-action">پس از تکمیل اطلاعات، به درگاه پرداخت منتقل می‌شوید.</p>
        <button type="button" onClick={() => void submitOrder()} className="checkout-primary-action mt-3 w-full rounded-lg border px-4 py-2 text-sm font-bold disabled:opacity-50" disabled={!cart.items.length || !localCustomerComplete || saving || submitting} aria-describedby="checkout-next-action">{submitting ? "در حال آماده‌سازی پرداخت…" : "ادامه به پرداخت"}</button>
      </form>
    </div>
  </main>;
}
