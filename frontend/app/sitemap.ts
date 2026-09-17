import type { MetadataRoute } from "next";
import { absoluteUrl } from "../lib/locale-url";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const routes = [
    { path: "", priority: 1.0, changeFrequency: "daily" as const },
    { path: "/shop", priority: 0.9, changeFrequency: "daily" as const },
    { path: "/categories", priority: 0.8, changeFrequency: "weekly" as const },
    { path: "/brands", priority: 0.8, changeFrequency: "weekly" as const },
    { path: "/capabilities", priority: 0.7, changeFrequency: "monthly" as const },
    { path: "/industries", priority: 0.7, changeFrequency: "monthly" as const },
    { path: "/about", priority: 0.7, changeFrequency: "monthly" as const },
    { path: "/contact", priority: 0.7, changeFrequency: "monthly" as const },
    { path: "/knowledge", priority: 0.7, changeFrequency: "weekly" as const },
    { path: "/faq", priority: 0.6, changeFrequency: "monthly" as const },
    { path: "/support/warranty", priority: 0.6, changeFrequency: "monthly" as const },
  ];

  return routes.flatMap(({ path, priority, changeFrequency }) => [
    { url: absoluteUrl(`/fa${path}`), lastModified: now, changeFrequency, priority },
    { url: absoluteUrl(`/en${path}`), lastModified: now, changeFrequency, priority },
  ]);
}
