type Location = { id: number; location_type: string; name_fa: string; name_en: string; address_fa: string; address_en: string; phone: string; mobile: string; email: string; working_hours: string };

const labels: Record<string, { fa: string; en: string }> = { factory: { fa: "کارخانه", en: "Factory" }, office: { fa: "دفتر", en: "Office" }, showroom: { fa: "نمایشگاه", en: "Showroom" }, store: { fa: "فروشگاه", en: "Store" }, representative: { fa: "نمایندگی", en: "Representative" } };

export function CompanyLocationCard({ location, locale }: { location: Location; locale: string }) {
  const english = locale === "en";
  const label = labels[location.location_type] || { fa: "مکان شرکت", en: "Company location" };
  const address = english && location.address_en ? location.address_en : location.address_fa;
  return <article className="company-location-card"><header><span>{english ? label.en : label.fa}</span><h3>{english && location.name_en ? location.name_en : location.name_fa}</h3></header>{address && <address>{address}</address>}<dl>{location.phone && <div><dt>{english ? "Phone" : "تلفن"}</dt><dd dir="ltr"><a href={`tel:${location.phone}`}>{location.phone}</a></dd></div>}{location.mobile && <div><dt>{english ? "Mobile" : "موبایل"}</dt><dd dir="ltr"><a href={`tel:${location.mobile}`}>{location.mobile}</a></dd></div>}{location.email && <div><dt>{english ? "Email" : "ایمیل"}</dt><dd dir="ltr"><a href={`mailto:${location.email}`}>{location.email}</a></dd></div>}{location.working_hours && <div><dt>{english ? "Hours" : "ساعات کاری"}</dt><dd>{location.working_hours}</dd></div>}</dl></article>;
}
