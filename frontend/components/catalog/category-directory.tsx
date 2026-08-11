"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { getCategoryUrl } from "../../lib/category-url";

type Category = { id: number; name_fa: string; slug: string; has_children: boolean };

function TreeNode({ category, locale }: { category: Category; locale: string }) {
  const [open, setOpen] = useState(false); const [children, setChildren] = useState<Category[]>([]);
  const toggle = () => { setOpen((value) => !value); if (!children.length && category.has_children) fetch(`/api/v1/categories/children/${category.id}/`).then((response) => response.json()).then(setChildren).catch(() => setChildren([])); };
  return <li><div><Link href={getCategoryUrl(category, locale)}>{category.name_fa}</Link>{category.has_children && <button type="button" onClick={toggle}>{open ? "↓" : locale === "fa" ? "←" : "→"}</button>}</div>{open && children.length > 0 && <ul>{children.map((child) => <TreeNode key={child.id} category={child} locale={locale} />)}</ul>}</li>;
}

export function CategoryDirectory() {
  const { locale = "fa" } = useParams<{ locale: string }>();
  const [roots, setRoots] = useState<Category[]>([]);
  useEffect(() => { fetch("/api/v1/categories/roots/").then((response) => response.json()).then(setRoots).catch(() => setRoots([])); }, []);
  return <main className="category-directory container-page"><div className="directory-breadcrumb"><Link href={`/${locale}`}>خانه</Link><span>‹</span><span>دسته‌بندی محصولات</span></div><section><header><p>کاتالوگ صنعتی</p><h1>دسته‌بندی محصولات</h1><span>برای مشاهده گروه‌ها، شاخه‌ها را باز کنید.</span></header><div className="directory-layout"><aside><b>فیلترهای کاتالوگ</b><p>فیلترهای فنی و موجودی در مرحله بعد به این بخش افزوده می‌شوند.</p></aside><div className="directory-tree"><ul>{roots.map((root) => <TreeNode key={root.id} category={root} locale={locale} />)}</ul></div><div className="directory-products"><b>محصولات دسته منتخب</b><p>با انتخاب هر دسته، محصولات مرتبط در این بخش نمایش داده می‌شوند.</p></div></div></section></main>;
}
