"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { useCompanyInfo } from "../../hooks/use-company-info";
import { CategoryNavigation } from "./category-navigation";
import { MainHeader } from "./main-header";
import { TopBar } from "./top-bar";
import type { Customer } from "../../services/auth-client";
import { currentUser, logout as logoutRequest, sessionStatus } from "../../lib/api/auth";
import type { CompanyInfo } from "../../types/api";

export function SiteHeader({ initialCompany = null }: { initialCompany?: CompanyInfo | null }) {
  const { locale = "fa" } = useParams<{ locale: string }>();
  const company = useCompanyInfo(initialCompany);
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [compact, setCompact] = useState(false);
  const compactRef = useRef(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const headerRef = useRef<HTMLElement>(null);
  useEffect(() => {
    const header = headerRef.current;
    if (!header) return;
    const updateOffset = () => document.documentElement.style.setProperty("--site-header-height", `${Math.ceil(header.getBoundingClientRect().height)}px`);
    updateOffset();
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(updateOffset);
    observer?.observe(header);
    window.addEventListener("resize", updateOffset);
    return () => { observer?.disconnect(); window.removeEventListener("resize", updateOffset); };
  }, [compact, menuOpen]);
  useEffect(() => {
    const load = (event?: Event) => {
      if (!event) {
        sessionStatus().then((result) => setCustomer(result.customer as Customer | null)).catch(() => setCustomer(null));
        return;
      }
      const authenticated = event instanceof CustomEvent && event.detail?.authenticated === true;
      if (!authenticated) { setCustomer(null); return; }
      currentUser().then((user) => setCustomer(user as Customer)).catch(() => setCustomer(null));
    };
    void load();
    window.addEventListener("auth-changed", load);
    return () => window.removeEventListener("auth-changed", load);
  }, []);
  useEffect(() => {
    let frame = 0;
    const updateHeader = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const next = compactRef.current ? window.scrollY > 24 : window.scrollY > 120;
        if (next !== compactRef.current) {
          compactRef.current = next;
          setCompact(next);
        }
      });
    };
    updateHeader();
    window.addEventListener("scroll", updateHeader, { passive: true });
    return () => { cancelAnimationFrame(frame); window.removeEventListener("scroll", updateHeader); };
  }, []);
  const logout = async () => { await logoutRequest(); setCustomer(null); window.dispatchEvent(new CustomEvent("auth-changed", { detail: { authenticated: false } })); };
  return <header ref={headerRef} className={`reference-header${compact ? " is-compact" : ""}${menuOpen ? " menu-is-open" : ""}`}><TopBar locale={locale} company={company} customer={customer} onLogout={logout} /><MainHeader locale={locale} company={company} menuOpen={menuOpen} onMenuToggle={() => setMenuOpen((value) => !value)} /><CategoryNavigation mobileOpen={menuOpen} onNavigate={() => setMenuOpen(false)} /></header>;
}
