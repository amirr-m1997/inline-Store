import type { MetadataRoute } from "next";
import { absoluteUrl } from "../lib/locale-url";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return [
    { url: absoluteUrl("/fa"), lastModified: now, changeFrequency: "daily", priority: 1 },
    { url: absoluteUrl("/en"), lastModified: now, changeFrequency: "daily", priority: 1 },
    { url: absoluteUrl("/fa/shop"), lastModified: now, changeFrequency: "daily", priority: 0.9 },
    { url: absoluteUrl("/en/shop"), lastModified: now, changeFrequency: "daily", priority: 0.9 },
  ];
}
