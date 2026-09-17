"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import type { SiteHero as SiteHeroData, SiteHeroBanner } from "../../types/api";

export function localizeHeroLink(link: string, locale: string) {
  return link.replace(/^\/(?:fa|en)(?=\/|$)/, `/${locale}`);
}

export function SiteHero({ hero, locale }: { hero: SiteHeroData | null; locale: string }) {
  const english = locale === "en";
  const banners = useMemo<SiteHeroBanner[]>(() => {
    if (!hero) return [];
    const legacyBanner = hero.hero_image || hero.mobile_hero_image ? {
      id: -1,
      desktop_image: hero.hero_image || "",
      mobile_image: hero.mobile_hero_image || hero.hero_image || "",
      title: hero.title,
      description: hero.description,
      button: hero.buttons[0] ? { text: hero.buttons[0].text, link: hero.buttons[0].link } : null,
    } : null;
    if (hero.banners?.length) return legacyBanner ? [legacyBanner, ...hero.banners] : hero.banners;
    return legacyBanner ? [legacyBanner] : [{ id: 0, desktop_image: "", mobile_image: "", title: hero.title, description: hero.description, button: hero.buttons[0] ? { text: hero.buttons[0].text, link: hero.buttons[0].link } : null }];
  }, [hero]);
  const [active, setActive] = useState(0);
  const [paused, setPaused] = useState(false);
  const liveRef = useRef<HTMLDivElement>(null);
  const prefersReducedMotion = useRef(false);

  useEffect(() => {
    prefersReducedMotion.current = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }, []);
  useEffect(() => {
    if (banners.length < 2 || paused || prefersReducedMotion.current) return;
    const timer = window.setInterval(() => setActive((value) => (value + 1) % banners.length), 3000);
    return () => window.clearInterval(timer);
  }, [banners.length, paused]);

  if (!hero || !banners.length) return <section className="site-hero site-hero-fallback site-container">
    <div className="site-hero-content">
      <h1>{english ? "Precise selection. Confident purchasing." : "انتخاب دقیق. خرید مطمئن."}</h1>
      <h2>{english ? "Specialist HVAC and refrigeration equipment" : "فروشگاه تخصصی تجهیزات و قطعات تهویه و تبرید"}</h2>
      <p>{english ? "A clear path from technical selection to supplying your project." : "از انتخاب فنی تا تأمین نیاز پروژه، محصولات و اطلاعات مورد نیازتان را در یک مسیر روشن پیدا کنید."}</p>
      <div className="site-hero-actions"><Link className="site-hero-button primary" href={`/${locale}/shop`}>{english ? "Browse products" : "مشاهده محصولات"}</Link><Link className="site-hero-button secondary" href={`/${locale}/rfq`}>{english ? "Get technical help" : "راهنمایی برای انتخاب"}</Link></div>
    </div>
  </section>;
  const banner = banners[active] || banners[0];
  const isLegacySlide = banner.id === -1 || (!hero.banners?.length && banner.id === 0);
  const move = (delta: number) => setActive((value) => (value + delta + banners.length) % banners.length);
  return <section className="site-hero site-container" onKeyDown={(event) => { if (event.key === "ArrowLeft") move(english ? 1 : -1); if (event.key === "ArrowRight") move(english ? -1 : 1); }} onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)} onFocus={() => setPaused(true)} onBlur={() => setPaused(false)} aria-roledescription={banners.length > 1 ? "carousel" : undefined} aria-label={banners.length > 1 ? (english ? "Homepage banners" : "بنرهای صفحه اصلی") : undefined}>
    {active === 0 && banner.desktop_image && <Image className="site-hero-media" alt={banner.title || (english ? "Homepage banner" : "بنر صفحه اصلی")} fill priority sizes="(max-width: 767px) 0px, min(100vw - 2rem, 1180px)" src={banner.desktop_image} />}
    {active !== 0 && banner.desktop_image && <Image className="site-hero-media" alt={banner.title || (english ? "Homepage banner" : "بنر صفحه اصلی")} fill loading="lazy" sizes="(max-width: 767px) 0px, min(100vw - 2rem, 1180px)" src={banner.desktop_image} />}
    {active === 0 && banner.mobile_image && <Image className="site-hero-media site-hero-media-mobile" alt={banner.title || (english ? "Homepage banner" : "بنر صفحه اصلی")} fill priority sizes="(max-width: 767px) min(100vw - 2rem, 1180px), 0px" src={banner.mobile_image} />}
    {active !== 0 && banner.mobile_image && <Image className="site-hero-media site-hero-media-mobile" alt={banner.title || (english ? "Homepage banner" : "بنر صفحه اصلی")} fill loading="lazy" sizes="(max-width: 767px) min(100vw - 2rem, 1180px), 0px" src={banner.mobile_image} />}
    <div className="site-hero-content" key={banner.id} aria-live="polite"><h1>{banner.title}</h1>{isLegacySlide ? hero.slogan && <h2>{hero.slogan}</h2> : banner.description && <h2>{banner.description}</h2>}{isLegacySlide && hero.description && <p>{hero.description}</p>}{(banner.button || (isLegacySlide && hero.buttons.length > 1)) && <div className="site-hero-actions">{banner.button && <Link className="site-hero-button primary" href={localizeHeroLink(banner.button.link, locale)}>{banner.button.text}</Link>}{isLegacySlide && hero.buttons.slice(1).map((button) => <Link key={button.link} className="site-hero-button secondary" href={localizeHeroLink(button.link, locale)}>{button.text}</Link>)}</div>}</div>
    {banners.length > 1 && <><button type="button" className="site-hero-control site-hero-control-prev" onClick={() => move(-1)} aria-label={english ? "Previous banner" : "بنر قبلی"}>‹</button><button type="button" className="site-hero-control site-hero-control-next" onClick={() => move(1)} aria-label={english ? "Next banner" : "بنر بعدی"}>›</button><div className="site-hero-indicators" role="group" aria-label={english ? "Choose homepage banner" : "انتخاب بنر صفحه اصلی"}>{banners.map((item, index) => <button key={item.id} type="button" className={index === active ? "is-active" : ""} onClick={() => setActive(index)} aria-label={`${english ? "Banner" : "بنر"} ${index + 1}`} aria-current={index === active ? "true" : undefined} />)}</div></>}
    <div ref={liveRef} className="sr-only" aria-live="polite">{english ? `Banner ${active + 1} of ${banners.length}` : `بنر ${active + 1} از ${banners.length}`}</div>
  </section>;
}
