"use client";

import { useEffect, useState } from "react";
import type { SiteHero } from "../types/api";

export function useSiteHero() {
  const [hero, setHero] = useState<SiteHero | null>(null);
  useEffect(() => { fetch("/api/v1/site/hero/", { cache: "no-store" }).then((response) => response.ok ? response.json() : null).then(setHero).catch(() => setHero(null)); }, []);
  return hero;
}
