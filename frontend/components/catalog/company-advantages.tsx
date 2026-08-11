"use client";

import { useEffect, useState } from "react";

type Advantage = { id: number; title_fa: string; description_fa: string; icon: string };

export function CompanyAdvantages() {
  const [advantages, setAdvantages] = useState<Advantage[]>([]);
  useEffect(() => { fetch("/api/v1/site/advantages/", { cache: "no-store" }).then((response) => response.ok ? response.json() : []).then(setAdvantages).catch(() => setAdvantages([])); }, []);
  return <section className="company-advantages site-container" aria-label="مزیت‌های شرکت"><div>{advantages.map((advantage) => <article key={advantage.id}><i>{advantage.icon}</i><div><h2>{advantage.title_fa}</h2>{advantage.description_fa && <p>{advantage.description_fa}</p>}</div></article>)}</div></section>;
}
