"use client";

import { useEffect, useState } from "react";

export function ThemeToggle() {
  const [dark, setDark] = useState(false);
  useEffect(() => {
    const saved = localStorage.getItem("theme");
    const isDark = saved ? saved === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    setDark(isDark); document.documentElement.classList.toggle("dark", isDark);
  }, []);
  const toggle = () => { const next = !dark; setDark(next); localStorage.setItem("theme", next ? "dark" : "light"); document.documentElement.classList.toggle("dark", next); };
  return <button className="theme-toggle" onClick={toggle} aria-label="تغییر تم">{dark ? "☀" : "☾"}</button>;
}
