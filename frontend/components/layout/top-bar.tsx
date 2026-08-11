"use client";
import Link from "next/link";
import { useState } from "react";
import type { Customer } from "../../services/auth-client";
import type { CompanyInfo } from "../../types/api";
export function TopBar({ company, customer, onLogout }: { company: CompanyInfo | null; customer: Customer | null; onLogout: () => void }) {
  const [open, setOpen] = useState(false);
  return <div className="reference-topbar"><div className="reference-topbar-inner site-container"><div className="reference-contact"><span>☎</span><span>{company?.phone || "..."}</span><span>{company?.address || "..."}</span></div><b>{company?.name_fa || "..."}</b>{customer ? <div className="customer-menu"><button type="button" onClick={() => setOpen((value) => !value)} aria-expanded={open}><span>♙</span>{customer.first_name || "حساب مشتری"}<i>⌄</i></button>{open && <div><Link href="/fa/account" onClick={() => setOpen(false)}>پروفایل من</Link><Link href="/fa/cart" onClick={() => setOpen(false)}>سبد خرید</Link><button type="button" onClick={onLogout}>خروج</button></div>}</div> : <Link href="/fa/login">ورود / ثبت‌نام مشتری <span>♙</span></Link>}</div></div>;
}
