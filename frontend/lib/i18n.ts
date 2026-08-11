export type Locale = "fa" | "en";
const locales = { fa: { code: "fa", lang: "fa-IR", dir: "rtl" as const }, en: { code: "en", lang: "en", dir: "ltr" as const } };
export const isLocale = (value: string): value is Locale => value === "fa" || value === "en";
export const getLocaleConfig = (locale: string) => locales[isLocale(locale) ? locale : "fa"];

