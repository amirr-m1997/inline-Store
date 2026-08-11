"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useCompanyInfo } from "../../../hooks/use-company-info";

type Advantage = { id: number; title_fa: string; description_fa: string; icon: string };

export default function AboutPage() {
  const company = useCompanyInfo();
  const [advantages, setAdvantages] = useState<Advantage[]>([]);
  useEffect(() => { fetch("/api/v1/site/advantages/").then((response) => response.ok ? response.json() : []).then(setAdvantages).catch(() => setAdvantages([])); }, []);
  if (!company) return <main className="public-page site-container"><div className="public-state">در حال دریافت اطلاعات شرکت…</div></main>;
  return <main className="public-page site-container">
    <nav className="public-breadcrumb"><Link href="/fa">خانه</Link><span>/</span><b>درباره ما</b></nav>
    <section className="about-hero">
      <div><span>درباره مجموعه</span><h1>{company.name_fa}</h1><p>{company.description || "اطلاعات معرفی شرکت به‌زودی تکمیل می‌شود."}</p><div><Link className="btn-primary" href="/fa/shop">مشاهده محصولات</Link><Link className="btn-secondary" href="/fa/contact">تماس با ما</Link></div></div>
      {company.logo && <div className="about-logo"><Image src={company.logo} alt={company.name_fa} width={240} height={180} sizes="(max-width: 700px) 160px, 240px" /></div>}
    </section>
    {advantages.length > 0 && <section className="about-values"><header><span>توانمندی‌ها و ارزش‌ها</span><h2>همراهی حرفه‌ای با صنعت</h2></header><div>{advantages.map((item) => <article key={item.id}><i aria-hidden="true">{item.icon || "✓"}</i><h3>{item.title_fa}</h3>{item.description_fa && <p>{item.description_fa}</p>}</article>)}</div></section>}
    <section className="about-contact-summary"><div><span>ارتباط با شرکت</span><h2>پاسخ‌گوی نیازهای تأمین و خرید شما هستیم</h2></div><dl>{company.phone && <div><dt>تلفن</dt><dd dir="ltr">{company.phone}</dd></div>}{company.email && <div><dt>ایمیل</dt><dd dir="ltr">{company.email}</dd></div>}{company.address && <div><dt>نشانی</dt><dd>{company.address}</dd></div>}{company.working_hours && <div><dt>ساعات کاری</dt><dd>{company.working_hours}</dd></div>}</dl></section>
  </main>;
}
