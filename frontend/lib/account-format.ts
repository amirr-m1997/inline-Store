export type AccountLocale = "fa" | "en";

export function accountLocaleTag(locale?: string) {
  return locale === "en" ? "en-US" : "fa-IR";
}

export function formatAccountNumber(value: number | string, locale?: string) {
  const number = typeof value === "number" ? value : Number(value);
  return Number.isFinite(number) ? number.toLocaleString(accountLocaleTag(locale)) : "—";
}

export function formatAccountDate(value: string, locale?: string, withTime = false) {
  return new Intl.DateTimeFormat(accountLocaleTag(locale), withTime ? { dateStyle: "medium", timeStyle: "short" } : { dateStyle: "long" }).format(new Date(value));
}
