import Image from "next/image";
import Link from "next/link";
import type { CompanyInfo } from "../../types/api";
import { CartButton } from "./cart-button";
import { SearchBar } from "./search-bar";
import { ThemeToggle } from "./theme-toggle";

type MainHeaderProps = { company: CompanyInfo | null; menuOpen: boolean; onMenuToggle: () => void };

export function MainHeader({ company, menuOpen, onMenuToggle }: MainHeaderProps) {
  return <div className="reference-main-header site-container"><Link className="reference-brand" href="/fa">{company?.logo ? <Image src={company.logo} alt={company.name_fa} width={64} height={64} /> : <i>{company?.name_fa.slice(0, 1) || "…"}</i>}<span><b>{company?.name_fa || "..."}</b><small>{company?.description || "..."}</small></span></Link><SearchBar /><div className="reference-actions"><CartButton /><ThemeToggle /><button className="reference-menu-toggle" type="button" aria-label="باز کردن منو" aria-expanded={menuOpen} onClick={onMenuToggle}><span /><span /><span /></button></div></div>;
}
