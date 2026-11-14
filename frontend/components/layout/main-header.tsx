import Image from "next/image";
import Link from "next/link";
import { FiUser, FiMenu, FiX } from "react-icons/fi";
import type { CompanyInfo } from "../../types/api";
import { CartButton } from "./cart-button";
import { SearchBar } from "./search-bar";
import { ThemeToggle } from "./theme-toggle";
import { Button } from "../ui/button";
import type { Customer } from "../../services/auth-client";

type MainHeaderProps = { locale: string; company: CompanyInfo | null; customer: Customer | null; menuOpen: boolean; onMenuToggle: () => void };

export function MainHeader({ locale, company, customer, menuOpen, onMenuToggle }: MainHeaderProps) {
  const english = locale === "en";
  return (
    <div className="reference-main-header responsive-container">
      <Link className={`reference-brand${company?.logo ? " reference-brand--logo" : ""}`} href={`/${locale}`} aria-label={`صفحه اصلی ${company?.name_fa || "فروشگاه"}`}>
        {company?.logo ? (
          <Image src={company.logo} alt="" aria-hidden="true" width={230} height={96} priority />
        ) : (
          <>
            <i aria-hidden="true">{company?.name_fa.slice(0, 1) || "…"}</i>
            <span><b>{company?.name_fa || "..."}</b></span>
          </>
        )}
      </Link>
      <SearchBar />
      <div className="reference-actions">
        <span className="reference-mobile-account-cart">
          <Link
            className="reference-mobile-account"
            href={`/${locale}/${customer ? "account" : "login"}`}
            aria-label={customer ? (english ? "Account" : "حساب کاربری") : (english ? "Sign in or register" : "ورود یا ثبت‌نام")}
          >
            <FiUser size={20} aria-hidden="true" />
          </Link>
          <CartButton locale={locale} />
        </span>
        <ThemeToggle />
        <Button
          variant="ghost"
          size="sm"
          className="reference-menu-toggle"
          aria-label={menuOpen ? "بستن منو" : "باز کردن منو"}
          aria-expanded={menuOpen}
          aria-controls="site-mobile-navigation"
          onClick={onMenuToggle}
        >
          {menuOpen ? <FiX size={22} aria-hidden="true" /> : <FiMenu size={22} aria-hidden="true" />}
        </Button>
      </div>
    </div>
  );
}
