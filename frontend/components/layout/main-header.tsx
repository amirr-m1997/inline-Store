import Image from "next/image";
import Link from "next/link";
import type { CompanyInfo } from "../../types/api";
import { CartButton } from "./cart-button";
import { SearchBar } from "./search-bar";
import { ThemeToggle } from "./theme-toggle";
import { Button } from "../ui/button";

type MainHeaderProps = { locale: string; company: CompanyInfo | null; menuOpen: boolean; onMenuToggle: () => void };

export function MainHeader({ locale, company, menuOpen, onMenuToggle }: MainHeaderProps) {
  const english = locale === "en";
  return <div className="reference-main-header responsive-container"><Link className={`reference-brand${company?.logo ? " reference-brand--logo" : ""}`} href={`/${locale}`} aria-label={`صفحه اصلی ${company?.name_fa || "فروشگاه"}`}>{company?.logo ? <Image src={company.logo} alt="" aria-hidden="true" width={230} height={96} priority /> : <><i aria-hidden="true">{company?.name_fa.slice(0, 1) || "…"}</i><span><b>{company?.name_fa || "..."}</b><small>{company?.description || "..."}</small></span></>}</Link><SearchBar /><div className="reference-actions"><span className="reference-header-ctas"><Button variant="primary" size="sm" href={`/${locale}/rfq`}>{english ? "Request Quote" : "درخواست پیش‌فاکتور"}</Button><Button variant="secondary" size="sm" href={`/${locale}/contact`}>{english ? "Contact Sales" : "تماس با فروش"}</Button></span><CartButton locale={locale} /><ThemeToggle /><Button variant="ghost" size="sm" className="reference-menu-toggle" aria-label={menuOpen ? "بستن منو" : "باز کردن منو"} aria-expanded={menuOpen} aria-controls="site-mobile-navigation" onClick={onMenuToggle}><span /><span /><span /></Button></div></div>;
}
