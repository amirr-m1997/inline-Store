"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FiHome, FiGrid, FiFileText, FiShoppingBag, FiUser } from "react-icons/fi";

interface MobileBottomNavProps {
  locale: string;
}

export function MobileBottomNav({ locale }: MobileBottomNavProps) {
  const pathname = usePathname() || "";
  const english = locale === "en";

  const navItems = [
    {
      id: "home",
      label: english ? "Home" : "خانه",
      href: `/${locale}`,
      icon: FiHome,
      isActive: pathname === `/${locale}` || pathname === `/${locale}/`,
    },
    {
      id: "categories",
      label: english ? "Categories" : "دسته‌ها",
      href: `/${locale}/categories`,
      icon: FiGrid,
      isActive: pathname.startsWith(`/${locale}/categories`) || pathname.startsWith(`/${locale}/category`),
    },
    {
      id: "rfq",
      label: english ? "RFQ Quote" : "استعلام",
      href: `/${locale}/rfq`,
      icon: FiFileText,
      isActive: pathname.startsWith(`/${locale}/rfq`),
      highlight: true,
    },
    {
      id: "cart",
      label: english ? "Cart" : "سبد خرید",
      href: `/${locale}/cart`,
      icon: FiShoppingBag,
      isActive: pathname.startsWith(`/${locale}/cart`),
    },
    {
      id: "account",
      label: english ? "Profile" : "پروفایل",
      href: `/${locale}/account`,
      icon: FiUser,
      isActive: pathname.startsWith(`/${locale}/account`) || pathname.startsWith(`/${locale}/login`),
    },
  ];

  return (
    <nav className="mobile-bottom-nav" aria-label={english ? "Mobile Navigation" : "ناوبری سریع موبایل"}>
      <div className="mobile-bottom-nav-inner">
        {navItems.map((item) => {
          const Icon = item.icon;
          const activeClass = item.isActive ? "is-active" : "";
          const highlightClass = item.highlight ? "is-highlight" : "";

          return (
            <Link
              key={item.id}
              href={item.href}
              className={`mobile-nav-link ${activeClass} ${highlightClass}`}
              aria-current={item.isActive ? "page" : undefined}
            >
              <div className="nav-icon-wrap">
                <Icon className="nav-icon" aria-hidden="true" />
              </div>
              <span className="nav-label">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}