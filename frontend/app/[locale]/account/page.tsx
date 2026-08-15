"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { Customer } from "../../../services/auth-client";
import { createAddress, deleteAddress, getAddresses, getProfile, updateProfile } from "../../../lib/api/account";
import { changePassword } from "../../../lib/api/auth";
import { getOrders, sendInvoice } from "../../../lib/api/orders";
import { formatAccountDate, formatAccountNumber } from "../../../lib/account-format";

type Address = { id: number; title: string; recipient_name: string; recipient_phone: string; province: string; city: string; postal_code: string; address: string; is_default: boolean };
type AddressDraft = Omit<Address, "id">;
type CustomerOrder = { id:number; order_number:string; status_label:string; created_at:string; final_amount:string; items_count:number };
const emptyAddress: AddressDraft = { title: "", recipient_name: "", recipient_phone: "", province: "", city: "", postal_code: "", address: "", is_default: false };
const emptyProfile: Customer = { id: 0, first_name: "", last_name: "", email: "", phone_number: "", landline: "", customer_type: "personal", company_name: "", national_id: "", economic_code: "", job_title: "", province: "", city: "", postal_code: "", address: "", date_joined: "" };

function normalizeProfile(value: Partial<Customer>): Customer {
  return {
    ...emptyProfile,
    ...value,
    customer_type: value.customer_type === "business" ? "business" : "personal",
    email: value.email ?? "",
    phone_number: value.phone_number ?? "",
    first_name: value.first_name ?? "",
    last_name: value.last_name ?? "",
    landline: value.landline ?? "",
    company_name: value.company_name ?? "",
    national_id: value.national_id ?? "",
    economic_code: value.economic_code ?? "",
    job_title: value.job_title ?? "",
    province: value.province ?? "",
    city: value.city ?? "",
    postal_code: value.postal_code ?? "",
    address: value.address ?? "",
    date_joined: value.date_joined ?? "",
  };
}

export default function AccountPage() {
  const { locale = "fa" } = useParams<{ locale: string }>();
  const router = useRouter();
  const [profile, setProfile] = useState<Customer | null>(null);
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [orders, setOrders] = useState<CustomerOrder[]>([]);
  const [sendingInvoice, setSendingInvoice] = useState<number | null>(null);
  const [draft, setDraft] = useState<AddressDraft>(emptyAddress);
  const [tab, setTab] = useState<"profile" | "addresses" | "invoices" | "activity" | "security">("profile");
  const [message, setMessage] = useState(""); const [error, setError] = useState("");

  const loadAddresses = () => getAddresses<Address[]>().then(setAddresses);
  useEffect(() => { getProfile<Customer>().then((value) => setProfile(normalizeProfile(value))).catch(() => router.replace(`/${locale}/login`)); loadAddresses().catch(() => setAddresses([])); getOrders<CustomerOrder[]>().then(setOrders).catch(() => setOrders([])); }, [locale, router]);
  const update = (name: keyof Customer, value: string) => setProfile((current) => current ? { ...current, [name]: value } : current);
  const saveProfile = async (event: React.FormEvent) => { event.preventDefault(); setError(""); setMessage(""); try { setProfile(normalizeProfile(await updateProfile<Customer>(profile))); setMessage("اطلاعات پروفایل ذخیره شد."); } catch (reason) { setError(reason instanceof Error ? reason.message : "درخواست ناموفق بود."); } };
  const addAddress = async (event: React.FormEvent) => { event.preventDefault(); setError(""); try { await createAddress<Address>(draft); setDraft(emptyAddress); await loadAddresses(); setMessage("نشانی جدید ثبت شد."); } catch (reason) { setError(reason instanceof Error ? reason.message : "درخواست ناموفق بود."); } };
  const removeAddress = async (id: number) => { try { await deleteAddress(id); await loadAddresses(); setMessage("نشانی حذف شد."); } catch (reason) { setError(reason instanceof Error ? reason.message : "حذف نشانی ناموفق بود."); } };
  const changePasswordAction = async (event: React.FormEvent<HTMLFormElement>) => { event.preventDefault(); setError(""); try { setMessage((await changePassword(Object.fromEntries(new FormData(event.currentTarget)))).detail); setTimeout(() => router.replace(`/${locale}/login`), 1200); } catch (reason) { setError(reason instanceof Error ? reason.message : "درخواست ناموفق بود."); } };
  const sendInvoiceAction = async (orderId:number) => { setError(""); setMessage(""); setSendingInvoice(orderId); try { const data = await sendInvoice<{ detail:string; recipient:string }>(orderId); setMessage(`${data.detail} گیرنده: ${data.recipient}`); } catch (reason) { setError(reason instanceof Error ? reason.message : "ارسال فاکتور ناموفق بود."); } finally { setSendingInvoice(null); } };

  const tabNames = ["profile", "addresses", "invoices", "activity", "security"] as const;
  const handleTabKey = (event: React.KeyboardEvent, current: typeof tabNames[number]) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const index = tabNames.indexOf(current);
    const next = event.key === "Home" ? 0 : event.key === "End" ? tabNames.length - 1 : (index + (event.key === "ArrowRight" ? 1 : -1) + tabNames.length) % tabNames.length;
    setTab(tabNames[next]);
    document.getElementById(`account-tab-${tabNames[next]}`)?.focus();
  };
  if (!profile) return <main className="account-page site-container"><p role="status" aria-live="polite">در حال دریافت حساب کاربری…</p></main>;
  return <main className="account-page site-container">
    <header className="account-heading"><div><span>پنل مشتری</span><h1>{profile.first_name || "مشتری"} {profile.last_name}</h1><p>عضویت از {formatAccountDate(profile.date_joined, locale)}</p></div><div className="account-heading-actions"><Link href={`/${locale}/account/support`}>{locale === "en" ? "Support" : "پشتیبانی"}</Link><Link href={`/${locale}/shop`}>ادامه خرید</Link></div></header>
    <nav className="account-tabs" role="tablist" aria-label={locale === "en" ? "Account sections" : "بخش‌های حساب کاربری"}><button id="account-tab-profile" role="tab" aria-selected={tab === "profile"} aria-controls="account-panel-profile" tabIndex={tab === "profile" ? 0 : -1} className={tab === "profile" ? "active" : ""} onKeyDown={(event) => handleTabKey(event, "profile")} onClick={() => setTab("profile")}>اطلاعات پروفایل</button><button id="account-tab-addresses" role="tab" aria-selected={tab === "addresses"} aria-controls="account-panel-addresses" tabIndex={tab === "addresses" ? 0 : -1} className={tab === "addresses" ? "active" : ""} onKeyDown={(event) => handleTabKey(event, "addresses")} onClick={() => setTab("addresses")}>نشانی‌ها <i>{formatAccountNumber(addresses.length, locale)}</i></button><Link href={`/${locale}/account/orders`}>{locale === "en" ? "My orders" : "سفارش‌های من"}</Link><Link href={`/${locale}/account/rfq`}>{locale === "en" ? "My RFQs" : "استعلام‌های قیمت"}</Link><button id="account-tab-invoices" role="tab" aria-selected={tab === "invoices"} aria-controls="account-panel-invoices" tabIndex={tab === "invoices" ? 0 : -1} className={tab === "invoices" ? "active" : ""} onKeyDown={(event) => handleTabKey(event, "invoices")} onClick={() => setTab("invoices")}>درخواست فاکتور رسمی</button><button id="account-tab-activity" role="tab" aria-selected={tab === "activity"} aria-controls="account-panel-activity" tabIndex={tab === "activity" ? 0 : -1} className={tab === "activity" ? "active" : ""} onKeyDown={(event) => handleTabKey(event, "activity")} onClick={() => setTab("activity")}>استعلام‌ها</button><button id="account-tab-security" role="tab" aria-selected={tab === "security"} aria-controls="account-panel-security" tabIndex={tab === "security" ? 0 : -1} className={tab === "security" ? "active" : ""} onKeyDown={(event) => handleTabKey(event, "security")} onClick={() => setTab("security")}>امنیت حساب</button></nav>
    <nav className="account-secondary-nav" aria-label={locale === "en" ? "Support" : "پشتیبانی"}><Link href={`/${locale}/account/support`}>{locale === "en" ? "Support" : "پشتیبانی"}</Link></nav>
    {message && <p className="account-message success" role="status" aria-live="polite">{message}</p>}{error && <p className="account-message error" role="alert">{error}</p>}
    {tab === "profile" && <form id="account-panel-profile" role="tabpanel" aria-labelledby="account-tab-profile" className="account-form" onSubmit={saveProfile}><section><h2>اطلاعات شخصی</h2><div className="account-fields"><label>نام<input value={profile.first_name} onChange={(e) => update("first_name", e.target.value)} /></label><label>نام خانوادگی<input value={profile.last_name} onChange={(e) => update("last_name", e.target.value)} /></label><label>ایمیل<input type="email" dir="ltr" value={profile.email || ""} onChange={(e) => update("email", e.target.value)} /></label><label>موبایل<input dir="ltr" value={profile.phone_number || ""} onChange={(e) => update("phone_number", e.target.value)} /></label><label>تلفن ثابت<input dir="ltr" value={profile.landline} onChange={(e) => update("landline", e.target.value)} /></label><label>نوع مشتری<select value={profile.customer_type} onChange={(e) => update("customer_type", e.target.value)}><option value="personal">شخصی</option><option value="business">حقوقی / سازمانی</option></select></label></div></section><section><h2>اطلاعات شرکت و فاکتور رسمی</h2><div className="account-fields"><label>نام شرکت<input value={profile.company_name} onChange={(e) => update("company_name", e.target.value)} /></label><label>سمت یا واحد سازمانی<input value={profile.job_title} onChange={(e) => update("job_title", e.target.value)} /></label><label>شناسه ملی<input dir="ltr" value={profile.national_id} onChange={(e) => update("national_id", e.target.value)} /></label><label>کد اقتصادی<input dir="ltr" value={profile.economic_code} onChange={(e) => update("economic_code", e.target.value)} /></label><label>استان<input value={profile.province} onChange={(e) => update("province", e.target.value)} /></label><label>شهر<input value={profile.city} onChange={(e) => update("city", e.target.value)} /></label><label>کدپستی<input dir="ltr" value={profile.postal_code} onChange={(e) => update("postal_code", e.target.value)} /></label><label className="wide">نشانی<textarea value={profile.address} onChange={(e) => update("address", e.target.value)} /></label></div></section><button className="btn-primary">ذخیره تغییرات</button></form>}
    {tab === "addresses" && <div id="account-panel-addresses" role="tabpanel" aria-labelledby="account-tab-addresses" className="address-layout"><section><h2>نشانی‌های تحویل</h2>{addresses.length ? <div className="address-list">{addresses.map((item) => <article key={item.id}><header><b>{item.title}</b>{item.is_default && <span>پیش‌فرض</span>}</header><p>{item.province}، {item.city}، {item.address}</p><small>{item.recipient_name} · <bdi dir="ltr">{item.recipient_phone}</bdi>{item.postal_code && ` · کدپستی ${item.postal_code}`}</small><button onClick={() => removeAddress(item.id)}>حذف نشانی</button></article>)}</div> : <p className="account-empty">هنوز نشانی تحویلی ثبت نشده است.</p>}</section><form onSubmit={addAddress}><h2>افزودن نشانی</h2><label>عنوان<input placeholder="مثلاً دفتر مرکزی" value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} required /></label><label>نام تحویل‌گیرنده<input value={draft.recipient_name} onChange={(e) => setDraft({ ...draft, recipient_name: e.target.value })} required /></label><label>شماره موبایل<input dir="ltr" value={draft.recipient_phone} onChange={(e) => setDraft({ ...draft, recipient_phone: e.target.value })} required /></label><div><label>استان<input value={draft.province} onChange={(e) => setDraft({ ...draft, province: e.target.value })} required /></label><label>شهر<input value={draft.city} onChange={(e) => setDraft({ ...draft, city: e.target.value })} required /></label></div><label>کدپستی<input dir="ltr" value={draft.postal_code} onChange={(e) => setDraft({ ...draft, postal_code: e.target.value })} /></label><label>نشانی<textarea value={draft.address} onChange={(e) => setDraft({ ...draft, address: e.target.value })} required /></label><label className="account-checkbox"><input type="checkbox" checked={draft.is_default} onChange={(e) => setDraft({ ...draft, is_default: e.target.checked })} /> نشانی پیش‌فرض</label><button className="btn-primary">ثبت نشانی</button></form></div>}
    {tab === "invoices" && <section id="account-panel-invoices" role="tabpanel" aria-labelledby="account-tab-invoices" className="account-invoice-panel"><header><div><span>اسناد مالی سفارش‌ها</span><h2>درخواست فاکتور رسمی</h2><p>فاکتور هر سفارش را مشاهده کنید یا به ایمیل ثبت‌شده در پروفایل بفرستید.</p></div><bdi dir="ltr">{profile.email || "ایمیل ثبت نشده"}</bdi></header>{!profile.email && <p className="account-message error">برای ارسال ایمیلی، ابتدا ایمیل خود را در بخش اطلاعات پروفایل ثبت و ذخیره کنید.</p>}{orders.length ? <div className="account-invoice-orders">{orders.map(order => <article key={order.id}><div><b dir="ltr">{order.order_number}</b><small>{formatAccountDate(order.created_at, locale)} · {order.status_label}</small></div><div><strong>{formatAccountNumber(order.final_amount, locale)} ریال</strong><small>{formatAccountNumber(order.items_count, locale)} کالا</small></div><div className="account-invoice-actions"><a href={`/api/customer/orders/${order.id}/invoice/?preview=1`} target="_blank" rel="noreferrer">مشاهده فاکتور</a><button disabled={!profile.email || sendingInvoice === order.id} onClick={() => sendInvoiceAction(order.id)}>{sendingInvoice === order.id ? "در حال ارسال…" : "ارسال به ایمیل"}</button></div></article>)}</div> : <p className="account-empty">برای مشاهده فاکتور، ابتدا باید سفارشی ثبت کرده باشید.</p>}</section>}
    {tab === "activity" && <div id="account-panel-activity" role="tabpanel" aria-labelledby="account-tab-activity" className="account-activity"><div><b>{locale === "en" ? "Request for quotation" : "درخواست استعلام قیمت"}</b><p>{locale === "en" ? "Submit product requirements for commercial review." : "نیاز محصول خود را برای بررسی تجاری ارسال کنید."}</p><Link href={`/${locale}/rfq`}>{locale === "en" ? "Submit an RFQ" : "ثبت استعلام قیمت"}</Link></div><div><b>پیش‌فاکتورها</b><strong>۰</strong><p>پیش‌فاکتورهای صادرشده در این بخش قرار می‌گیرند.</p></div><div><b>سفارش‌ها</b><p>سوابق کامل، وضعیت ارسال و فاکتورهای خود را ببینید.</p><Link href={`/${locale}/account/orders`}>مشاهده سفارش‌های من</Link></div></div>}
    {tab === "security" && <form id="account-panel-security" role="tabpanel" aria-labelledby="account-tab-security" className="security-form" onSubmit={changePasswordAction}><h2>تغییر رمز عبور</h2><p>برای امنیت بیشتر، رمز جدید را متفاوت از اطلاعات شخصی خود انتخاب کنید.</p><label>رمز عبور فعلی<input name="current_password" type="password" autoComplete="current-password" required /></label><label>رمز عبور جدید<input name="password" type="password" autoComplete="new-password" required /></label><label>تکرار رمز جدید<input name="password_confirm" type="password" autoComplete="new-password" required /></label><button className="btn-primary">تغییر رمز عبور</button></form>}
  </main>;
}
