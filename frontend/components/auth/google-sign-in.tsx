"use client";

import { useEffect, useRef, useState } from "react";
import { authChanged, mergeGuestCart } from "../../services/auth-client";
import { googleSignIn } from "../../lib/api/auth";

declare global { interface Window { google?: { accounts: { id: { initialize(config: { client_id: string; callback: (result: { credential: string }) => void }): void; renderButton(element: HTMLElement, options: Record<string, unknown>): void } } } } }

export function GoogleSignIn({ onSuccess, label = "signin_with", locale = "fa" }: { onSuccess: () => void; label?: "signin_with" | "signup_with" | "continue_with"; locale?: string }) {
  const container = useRef<HTMLDivElement>(null); const [error, setError] = useState("");
  useEffect(() => {
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    if (!clientId) return;
    const setup = () => { if (!window.google || !container.current) return; window.google.accounts.id.initialize({ client_id: clientId, callback: async ({ credential }) => { try { await googleSignIn(credential); await mergeGuestCart(); authChanged(); onSuccess(); } catch (reason) { setError(reason instanceof Error ? reason.message : "درخواست ناموفق بود."); } } }); const width = Math.min(320, container.current.clientWidth || 320); window.google.accounts.id.renderButton(container.current, { theme: "outline", size: "large", width, locale: locale === "en" ? "en" : "fa", text: label, shape: "rectangular" }); };
    const existing = document.querySelector<HTMLScriptElement>('script[src="https://accounts.google.com/gsi/client"]');
    if (existing) { if (window.google) setup(); else existing.addEventListener("load", setup, { once: true }); return; }
    const script = document.createElement("script"); script.src = "https://accounts.google.com/gsi/client"; script.async = true; script.onload = setup; document.head.appendChild(script);
  }, [label, locale, onSuccess]);
  if (!process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID) return null;
  return <div className="google-auth w-full max-w-[320px]"><div ref={container} />{error && <p>{error}</p>}</div>;
}
