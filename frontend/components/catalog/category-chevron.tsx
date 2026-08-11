export function CategoryChevron({ open = false, locale = "fa" }: { open?: boolean; locale?: string }) {
  return <span className="category-chevron" aria-hidden="true">{open ? "↓" : locale === "fa" ? "←" : "→"}</span>;
}
