"use client";

import { useEffect, useRef } from "react";
import type { ReactNode } from "react";

export function Drawer({ open, onClose, title, children, className = "", overlayClassName = "" }: { open: boolean; onClose: () => void; title: string; children: ReactNode; className?: string; overlayClassName?: string }) {
  const drawerRef = useRef<HTMLDivElement>(null); const closeRef = useRef<HTMLButtonElement>(null);
  useEffect(() => { if (!open) return; const previous = document.activeElement as HTMLElement | null; const previousOverflow = document.body.style.overflow; document.body.style.overflow = "hidden"; closeRef.current?.focus(); const onKeyDown = (event: KeyboardEvent) => { if (event.key === "Escape") { event.preventDefault(); onClose(); return; } if (event.key !== "Tab") return; const focusable = drawerRef.current?.querySelectorAll<HTMLElement>('button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'); if (!focusable?.length) return; const first = focusable[0]; const last = focusable[focusable.length - 1]; if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); } else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); } }; document.addEventListener("keydown", onKeyDown); return () => { document.removeEventListener("keydown", onKeyDown); document.body.style.overflow = previousOverflow; previous?.focus(); }; }, [onClose, open]);
  if (!open) return null;
  return <div className={`ui-overlay ui-drawer-overlay ${overlayClassName}`} role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><div ref={drawerRef} className={`ui-drawer ${className}`} role="dialog" aria-modal="true" aria-labelledby="shared-drawer-title" onMouseDown={(event) => event.stopPropagation()}><div className="ui-drawer-header"><h2 id="shared-drawer-title">{title}</h2><button ref={closeRef} type="button" onClick={onClose} aria-label="بستن">×</button></div>{children}</div></div>;
}
