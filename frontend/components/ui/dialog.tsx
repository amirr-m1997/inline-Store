"use client";

import { useEffect, useRef } from "react";
import type { ReactNode } from "react";

export function Dialog({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: ReactNode }) {
  const closeRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLElement>(null);
  useEffect(() => { if (!open) return; const previous = document.activeElement as HTMLElement | null; closeRef.current?.focus(); const onKeyDown = (event: KeyboardEvent) => { if (event.key === "Escape") return onClose(); if (event.key !== "Tab") return; const focusable = dialogRef.current?.querySelectorAll<HTMLElement>('button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'); if (!focusable?.length) return; const first = focusable[0]; const last = focusable[focusable.length - 1]; if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); } else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); } }; document.addEventListener("keydown", onKeyDown); return () => { document.removeEventListener("keydown", onKeyDown); previous?.focus(); }; }, [onClose, open]);
  if (!open) return null;
  return <div className="ui-overlay" role="presentation" onMouseDown={onClose}><section ref={dialogRef} className="ui-dialog" role="dialog" aria-modal="true" aria-label={title} onMouseDown={(event) => event.stopPropagation()}><header><h2>{title}</h2><button ref={closeRef} type="button" onClick={onClose} aria-label="بستن">×</button></header>{children}</section></div>;
}
