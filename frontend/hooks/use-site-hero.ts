"use client";

import { useEffect, useState } from "react";
import type { SiteHero } from "../types/api";
import { getHero } from "../lib/api/content";

export function useSiteHero() {
  const [hero, setHero] = useState<SiteHero | null>(null);
  useEffect(() => { getHero<SiteHero>().then(setHero).catch(() => setHero(null)); }, []);
  return hero;
}
