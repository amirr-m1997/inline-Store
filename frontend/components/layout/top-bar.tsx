"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import type { Customer } from "../../services/auth-client";
import type { CompanyInfo } from "../../types/api";
export function TopBar({ locale, company, customer, onLogout }: { locale: string; company: CompanyInfo | null; customer: Customer | null; onLogout: () => void }) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  useEffect(() => { if (!open) return; const closeOnOutside = (event: PointerEvent) => { if (!menuRef.current?.contains(event.target as Node)) setOpen(false); }; const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape") setOpen(false); }; document.addEventListener("pointerdown", closeOnOutside); document.addEventListener("keydown", closeOnEscape); return () => { document.removeEventListener("pointerdown", closeOnOutside); document.removeEventListener("keydown", closeOnEscape); }; }, [open]);
  return <div className="reference-topbar"><div className="reference-topbar-inner site-container"><div className="reference-contact"><span aria-hidden="true">☎</span><span>{company?.phone || "..."}</span><span>{company?.address || "..."}</span></div><b>{company?.name_fa || "..."}</b>{customer ? <div ref={menuRef} className="customer-menu"><button id="customer-menu-trigger" type="button" onClick={() => setOpen((value) => !value)} aria-label="منوی حساب کاربری" aria-expanded={open} aria-controls="customer-menu-panel"><span aria-hidden="true">♙</span>{customer.first_name || "حساب مشتری"}<i aria-hidden="true">⌄</i></button>{open && <div id="customer-menu-panel" role="menu"><Link role="menuitem" href={`/${locale}/account`} onClick={() => setOpen(false)}>پروفایل من</Link><Link role="menuitem" href={`/${locale}/cart`} onClick={() => setOpen(false)}>سبد خرید</Link><button role="menuitem" type="button" onClick={onLogout}>خروج</button></div>}</div> : <Link href={`/${locale}/login`}>ورود / ثبت‌نام مشتری <span aria-hidden="true">♙</span></Link>}</div></div>;
}
