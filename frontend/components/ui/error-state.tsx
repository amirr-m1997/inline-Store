import type { ReactNode } from "react";

export function ErrorState({ title = "دریافت اطلاعات ناموفق بود", description, action }: { title?: string; description?: string; action?: ReactNode }) {
  return <section className="ui-state ui-state--error" role="alert"><b>{title}</b>{description && <p>{description}</p>}{action && <div>{action}</div>}</section>;
}
