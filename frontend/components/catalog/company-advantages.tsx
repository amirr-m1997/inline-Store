export type Advantage = { id: number; title_fa: string; title_en?: string; description_fa: string; description_en?: string; icon: string };

export function CompanyAdvantages({ advantages }: { advantages: Advantage[] }) {
  return <section className="company-advantages site-container" aria-label="مزیت‌های شرکت"><div>{advantages.map((advantage) => <article key={advantage.id}><i aria-hidden="true">{advantage.icon}</i><div><h2>{advantage.title_fa}</h2>{advantage.description_fa && <p>{advantage.description_fa}</p>}</div></article>)}</div></section>;
}
