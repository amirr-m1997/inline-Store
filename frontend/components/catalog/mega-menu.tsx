"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { getCategoryUrl } from "../../lib/category-url";

export type NavCategory = { id: number; name_fa: string; slug: string; has_children: boolean };

function Branch({ category, locale }: { category: NavCategory; locale: string }) {
  const [children, setChildren] = useState<NavCategory[]>([]);
  const [loaded, setLoaded] = useState(false);
  const load = () => {
    if (loaded || !category.has_children) return;
    fetch(`/api/v1/categories/children/${category.id}/`).then((response) => response.json()).then((data) => { setChildren(data); setLoaded(true); }).catch(() => setLoaded(true));
  };
  return <div className="mega-branch" onMouseEnter={load}><Link href={getCategoryUrl(category, locale)}>{category.name_fa}</Link>{children.length > 0 && <div>{children.map((child) => <Link key={child.id} href={getCategoryUrl(child, locale)}>{child.name_fa}</Link>)}</div>}</div>;
}

export function MegaMenu() {
  const { locale = "fa" } = useParams<{ locale: string }>();
  const [roots, setRoots] = useState<NavCategory[]>([]);
  const [active, setActive] = useState<NavCategory | null>(null);
  const [children, setChildren] = useState<NavCategory[]>([]);
  useEffect(() => { fetch("/api/v1/categories/roots/").then((response) => response.json()).then(setRoots).catch(() => setRoots([])); }, []);
  const open = (root: NavCategory) => {
    setActive(root);
    fetch(`/api/v1/categories/children/${root.id}/`).then((response) => response.json()).then(setChildren).catch(() => setChildren([]));
  };
  return <nav className="mega-nav" onMouseLeave={() => setActive(null)}>{roots.map((root) => <button key={root.id} onMouseEnter={() => open(root)} onFocus={() => open(root)}><Link href={getCategoryUrl(root, locale)}>{root.name_fa}</Link></button>)}{active && <section className="mega-panel"><div className="mega-heading"><span>دسته‌بندی اصلی</span><Link href={getCategoryUrl(active, locale)}>{active.name_fa}</Link></div><div className="mega-columns">{children.map((category) => <Branch key={category.id} category={category} locale={locale} />)}</div></section>}</nav>;
}
