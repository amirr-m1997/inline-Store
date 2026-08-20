"use client";

import { useEffect, useState } from "react";

export function ThemeToggle() {
  const [dark, setDark] = useState(false);
  useEffect(() => {
    setDark(document.documentElement.classList.contains("dark"));
  }, []);
  const toggle = () => {
    const root = document.documentElement;
    const next = !root.classList.contains("dark");
    setDark(next);
    root.classList.add("theme-changing");
    root.classList.toggle("dark", next);
    try {
      localStorage.setItem("theme", next ? "dark" : "light");
    } catch {
      // Theme still applies for this session when storage is unavailable.
    }
    window.requestAnimationFrame(() => root.classList.remove("theme-changing"));
  };
  return <button type="button" className="theme-toggle" onClick={toggle} aria-label="تغییر تم" aria-pressed={dark} title={dark ? "بازگشت به تم روشن" : "فعال‌کردن تم تاریک"}>{dark ? "☀" : "☾"}</button>;
}
