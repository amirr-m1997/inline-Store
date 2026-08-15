import { CompanyLocationCard } from "./company-location-card";

export function CompanyLocationGroups({ locations, locale, showHeader = true, compact = false }: { locations: Parameters<typeof CompanyLocationCard>[0]["location"][]; locale: string; showHeader?: boolean; compact?: boolean }) {
  if (!locations.length) return null;
  const english = locale === "en";
  const groups = new Map<string, typeof locations>();
  locations.forEach((location) => groups.set(location.location_type, [...(groups.get(location.location_type) || []), location]));
  return <section className={`company-locations${compact ? " company-locations--compact" : ""}`} aria-labelledby={showHeader ? "company-locations-title" : undefined}>{showHeader && <header><span>{english ? "Published locations" : "مکان‌های منتشرشده"}</span><h2 id="company-locations-title">{english ? "Facilities and offices" : "مراکز و دفاتر"}</h2></header>}{Array.from(groups.entries()).map(([type, items]) => <div className="company-location-group" key={type}><h3>{({ factory: english ? "Factories" : "کارخانه‌ها", office: english ? "Offices" : "دفاتر", showroom: english ? "Showrooms" : "نمایشگاه‌ها", store: english ? "Stores" : "فروشگاه‌ها", representative: english ? "Representatives" : "نمایندگی‌ها" } as Record<string, string>)[type] || (english ? "Other locations" : "سایر مکان‌ها")}</h3><div className="company-location-grid">{items.map((location) => <CompanyLocationCard key={location.id} location={location} locale={locale} />)}</div></div>)}</section>;
}
