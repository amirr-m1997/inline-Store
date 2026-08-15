import Link from "next/link";
import Image from "next/image";
import type { SiteHero as SiteHeroData } from "../../types/api";

export function localizeHeroLink(link: string, locale: string) {
  return link.replace(/^\/(?:fa|en)(?=\/|$)/, `/${locale}`);
}

export function SiteHero({ hero, locale }: { hero: SiteHeroData | null; locale: string }) {
  if (!hero) return <section className="site-hero site-hero-loading site-container" />;
  return <section className="site-hero site-container">{hero.hero_image && <Image className="site-hero-media" alt="" fill priority sizes="(max-width: 767px) 0px, min(100vw - 2rem, 1180px)" src={hero.hero_image} />}{hero.mobile_hero_image && <Image className="site-hero-media site-hero-media-mobile" alt="" fill priority sizes="(max-width: 767px) min(100vw - 2rem, 1180px), 0px" src={hero.mobile_hero_image} />}<div className="site-hero-content"><h1>{hero.title}</h1><h2>{hero.slogan}</h2>{hero.description && <p>{hero.description}</p>}<div className="site-hero-actions">{hero.buttons.map((button, index) => <Link key={`${button.variant}-${button.link}`} className={`site-hero-button ${index === 0 ? "primary" : "secondary"}`} href={localizeHeroLink(button.link, locale)}>{button.text}</Link>)}</div></div></section>;
}
