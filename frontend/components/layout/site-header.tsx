"use client";

import { useEffect, useRef, useState } from "react";
import { useCompanyInfo } from "../../hooks/use-company-info";
import { CategoryNavigation } from "./category-navigation";
import { MainHeader } from "./main-header";
import { TopBar } from "./top-bar";
import type { Customer } from "../../services/auth-client";

export function SiteHeader() {
  const company = useCompanyInfo();
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [compact, setCompact] = useState(false);
  const compactRef = useRef(false);
  const [menuOpen, setMenuOpen] = useState(false);
  useEffect(() => { const load = () => fetch("/api/v1/auth/profile/", { cache: "no-store" }).then((response) => response.ok ? response.json() : null).then(setCustomer).catch(() => setCustomer(null)); void load(); window.addEventListener("auth-changed", load); return () => window.removeEventListener("auth-changed", load); }, []);
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
  const logout = async () => { await fetch("/api/v1/auth/logout/", { method: "POST" }); setCustomer(null); window.dispatchEvent(new Event("auth-changed")); };
  return <header className={`reference-header${compact ? " is-compact" : ""}${menuOpen ? " menu-is-open" : ""}`}><TopBar company={company} customer={customer} onLogout={logout} /><MainHeader company={company} menuOpen={menuOpen} onMenuToggle={() => setMenuOpen((value) => !value)} /><CategoryNavigation mobileOpen={menuOpen} onNavigate={() => setMenuOpen(false)} /></header>;
}
