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
    localStorage.setItem("theme", next ? "dark" : "light");
    root.classList.add("theme-changing");
    root.classList.toggle("dark", next);
    window.requestAnimationFrame(() => root.classList.remove("theme-changing"));
  };
  return <button className="theme-toggle" onClick={toggle} aria-label="تغییر تم">{dark ? "☀" : "☾"}</button>;
}
