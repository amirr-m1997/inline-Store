export const supportedLocales = ["fa", "en"] as const;
export type SupportedLocale = (typeof supportedLocales)[number];

export function siteOrigin() {
  return (process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000").replace(/\/$/, "");
}

export function absoluteUrl(path: string) {
  return new URL(path, `${siteOrigin()}/`).toString();
}

export function localizedPath(locale: string, path = "") {
  return `/${locale}${path.startsWith("/") || !path ? path : `/${path}`}`;
}

export function localizedAlternates(path = "") {
  return {
    languages: {
      fa: absoluteUrl(localizedPath("fa", path)),
      en: absoluteUrl(localizedPath("en", path)),
      "x-default": absoluteUrl(localizedPath("fa", path)),
    },
  };
}
