"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";

type FooterPayload = {
  company: { name_fa: string; logo: string | null; description: string; phone: string; mobile: string; email: string; address: string; website: string } | null;
  sections: { id: number; title: string; links: { id: number; title: string; url: string; open_in_new_tab: boolean }[] }[];
  trust_badges: { id: number; title: string; image: string; url: string; alt: string }[];
  copyright: string;
};

const isInternal = (url: string) => url.startsWith("/");

export function SiteFooter() {
  const [footer, setFooter] = useState<FooterPayload | null>(null);
  useEffect(() => {
    fetch("/api/v1/site/footer/", { cache: "no-store" }).then((response) => response.ok ? response.json() : null).then(setFooter).catch(() => setFooter(null));
  }, []);
  if (!footer) return <footer className="database-footer footer-loading" aria-hidden="true" />;
  const company = footer.company;
  return <footer className="database-footer">
    <div className="footer-main site-container">
      {company && <section className="footer-company" aria-label={company.name_fa}>
        <div className="footer-brand">{company.logo && <Image src={company.logo} alt={company.name_fa} width={92} height={92} sizes="92px" />}<h2>{company.name_fa}</h2></div>
        {company.description && <p>{company.description}</p>}
        <address>{company.address && <span>{company.address}</span>}{company.phone && <a href={`tel:${company.phone}`} dir="ltr">{company.phone}</a>}{company.mobile && <a href={`tel:${company.mobile}`} dir="ltr">{company.mobile}</a>}{company.email && <a href={`mailto:${company.email}`} dir="ltr">{company.email}</a>}</address>
      </section>}

      <nav className="footer-sections" aria-label="پیوندهای پایین سایت">{footer.sections.map((section) => <section key={section.id}><h2>{section.title}</h2><ul>{section.links.map((link) => <li key={link.id}>{isInternal(link.url) && !link.open_in_new_tab ? <Link href={link.url}>{link.title}<span aria-hidden="true">←</span></Link> : <a href={link.url} target={link.open_in_new_tab ? "_blank" : undefined} rel={link.open_in_new_tab ? "noreferrer" : undefined}>{link.title}<span aria-hidden="true">←</span></a>}</li>)}</ul></section>)}</nav>

      {footer.trust_badges.length > 0 && <section className="footer-trust" aria-label="نشان‌های اعتماد">{footer.trust_badges.map((badge) => { const image = <Image src={badge.image} alt={badge.alt} width={110} height={110} sizes="110px" />; return <div key={badge.id}>{badge.url ? <a href={badge.url} target="_blank" rel="noreferrer" title={badge.title}>{image}</a> : image}</div>; })}</section>}
    </div>
    {footer.copyright && <div className="footer-bottom"><p className="site-container">{footer.copyright}</p></div>}
  </footer>;
}
