"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { FiPhone, FiUser, FiChevronDown, FiShoppingCart, FiLogOut, FiMapPin, FiPackage } from "react-icons/fi";
import type { Customer } from "../../services/auth-client";
import type { CompanyInfo } from "../../types/api";

export function TopBar({ locale, company, customer, onLogout }: { locale: string; company: CompanyInfo | null; customer: Customer | null; onLogout: () => void }) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const english = locale === "en";

  useEffect(() => {
    if (!open) return;
    const closeOnOutside = (event: PointerEvent) => { if (!menuRef.current?.contains(event.target as Node)) setOpen(false); };
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape") setOpen(false); };
    document.addEventListener("pointerdown", closeOnOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOnOutside);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [open]);

  return (
    <div className="reference-topbar">
      <div className="reference-topbar-inner responsive-container">
        {/* سمت راست: تماس و آدرس داینامیک */}
        <div className="reference-contact">
          <a href={`tel:${company?.phone || ""}`} className="topbar-phone-pill" aria-label={`تماس تلفنی با ${company?.phone || "شرکت"}`}>
            <span className="topbar-status-dot" aria-hidden="true" />
            <FiPhone size={12} className="topbar-phone-icon" aria-hidden="true" />
            <span className="topbar-phone-text" dir="ltr">{company?.phone || "..."}</span>
          </a>
          <span className="topbar-divider" aria-hidden="true" />
          <div className="topbar-address-wrap">
            <FiMapPin size={13} className="topbar-pin-icon" aria-hidden="true" />
            <span className="topbar-address-text">{company?.address || "..."}</span>
          </div>
        </div>

        {/* سمت چپ: پیگیری سفارش و دسترسی کاربری */}
        <div className="topbar-user-section">
          <Link href={`/${locale}/account/orders`} className="topbar-order-tracking" aria-label={english ? "Track order" : "پیگیری سفارش"}>
            <FiPackage size={13} aria-hidden="true" />
            <span>{english ? "Track Order" : "پیگیری سفارش"}</span>
          </Link>
          <span className="topbar-divider" aria-hidden="true" />
          {customer ? (
            <div ref={menuRef} className="customer-menu">
              <button id="customer-menu-trigger" className="customer-pill-button" type="button" onClick={() => setOpen((value) => !value)} aria-label="منوی حساب کاربری" aria-expanded={open} aria-controls="customer-menu-panel">
                <span className="customer-avatar-icon" aria-hidden="true">
                  <FiUser size={13} aria-hidden="true" />
                </span>
                <span className="customer-user-name">{customer.first_name || "حساب مشتری"}</span>
                <i className="customer-dropdown-arrow" aria-hidden="true"><FiChevronDown size={12} aria-hidden="true" /></i>
              </button>
              {open && (
                <div id="customer-menu-panel" role="menu">
                  <Link role="menuitem" href={`/${locale}/account`} onClick={() => setOpen(false)}>
                    <FiUser size={13} aria-hidden="true" style={{ display: "inline-block", marginInlineEnd: 6 }} />
                    پروفایل من
                  </Link>
                  <Link role="menuitem" href={`/${locale}/cart`} onClick={() => setOpen(false)}>
                    <FiShoppingCart size={13} aria-hidden="true" style={{ display: "inline-block", marginInlineEnd: 6 }} />
                    سبد خرید
                  </Link>
                  <button role="menuitem" type="button" onClick={onLogout}>
                    <FiLogOut size={13} aria-hidden="true" style={{ display: "inline-block", marginInlineEnd: 6 }} />
                    خروج
                  </button>
                </div>
              )}
            </div>
          ) : (
            <Link href={`/${locale}/login`} className="topbar-auth-pill">
              <span className="topbar-auth-avatar" aria-hidden="true">
                <FiUser size={12} aria-hidden="true" />
              </span>
              <span>ورود / ثبت‌نام مشتری</span>
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
