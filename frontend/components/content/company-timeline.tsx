type Milestone = { id: number; date_label: string; title_fa: string; title_en: string; description_fa: string; description_en: string };

export function CompanyTimeline({ milestones, locale }: { milestones: Milestone[]; locale: string }) {
  if (!milestones.length) return null;
  const english = locale === "en";
  const display = (value: string) => value.replace(/^\[DEMO\]\s*/i, "");
  return <section className={`company-timeline ${milestones.length === 1 ? "company-timeline--single" : ""}`} aria-labelledby="company-history-title"><header><span>{english ? "Company record" : "سوابق ثبت‌شده شرکت"}</span><h2 id="company-history-title">{english ? "History" : "تاریخچه شرکت"}</h2></header><ol>{milestones.map((milestone) => { const title = english && milestone.title_en ? milestone.title_en : milestone.title_fa; const description = english ? milestone.description_en || milestone.description_fa : milestone.description_fa; return <li key={milestone.id}><div className="company-timeline-marker" aria-hidden="true" /><div><time>{milestone.date_label}</time><h3>{display(title)}{title.startsWith("[DEMO]") && <span className="content-demo-indicator">{english ? "Demo" : "نمونه"}</span>}</h3>{description && <p>{description}</p>}</div></li>; })}</ol></section>;
}
