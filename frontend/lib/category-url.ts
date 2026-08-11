export type CategoryUrlSource = { slug: string };

export function getCategoryUrl(category: CategoryUrlSource, locale: string) {
  return `/${locale}/category/${encodeURIComponent(category.slug)}`;
}

export function getCategorySearchUrl(locale: string, query = "") {
  const suffix = query ? `?q=${encodeURIComponent(query)}` : "";
  return `/${locale}/category/search${suffix}`;
}
