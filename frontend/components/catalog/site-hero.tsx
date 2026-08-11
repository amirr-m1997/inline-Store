"use client";

import Link from "next/link";
import type { CSSProperties } from "react";
import { useSiteHero } from "../../hooks/use-site-hero";

export function SiteHero() {
  const hero = useSiteHero();
  if (!hero) return <section className="site-hero site-hero-loading site-container" />;
  const style = hero.hero_image ? { "--hero-desktop": `url(${hero.hero_image})`, "--hero-mobile": `url(${hero.mobile_hero_image || hero.hero_image})` } as CSSProperties : undefined;
  return <section className="site-hero site-container" style={style}><div><h1>{hero.title}</h1><h2>{hero.slogan}</h2>{hero.description && <p>{hero.description}</p>}<div className="site-hero-actions">{hero.buttons.map((button) => <Link key={`${button.variant}-${button.link}`} className={button.variant} href={button.link}>{button.text}</Link>)}</div></div></section>;
}
