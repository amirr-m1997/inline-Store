import type { ReactNode } from "react";

export function EmptyState({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return <section className="ui-state ui-state--empty"><b>{title}</b>{description && <p>{description}</p>}{action && <div>{action}</div>}</section>;
}
