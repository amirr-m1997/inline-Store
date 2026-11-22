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
      label: english ? "Quote" : "استعلام",
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
    <nav className="mobile-bottom-nav-bar" aria-label={english ? "Mobile Navigation" : "ناوبری همراه"}>
      <div className="mobile-bottom-nav-container">
        {navItems.map((item) => {
          const Icon = item.icon;
          const activeClass = item.isActive ? "is-active" : "";
          const highlightClass = item.highlight ? "is-rfq-center" : "";

          return (
            <Link
              key={item.id}
              href={item.href}
              className={`mobile-bottom-nav-item ${activeClass} ${highlightClass}`}
              aria-current={item.isActive ? "page" : undefined}
            >
              <div className="item-icon-box">
                <Icon aria-hidden="true" />
              </div>
              <span className="item-label">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}