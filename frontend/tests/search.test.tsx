import { render, screen } from "@testing-library/react";
import fs from "node:fs";
import path from "node:path";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/link", () => ({ default: ({ href, children, ...props }: { href: string; children: React.ReactNode }) => <a href={href} {...props}>{children}</a> }));

import { SearchCategoryGroup, SearchEditorialGroup, SearchEntryForm, SearchGroupSummary, SearchProductGroup } from "../components/search/search-results";

const product = { id: 1, slug: "chiller", code: "CH-1", name: "Chiller", name_fa: "چیلر", name_en: "Chiller", unit: "عدد", image: null, category: { id: 1, slug: "hvac", name_fa: "تهویه", name_en: "HVAC" }, brand: null };
const article = { id: 2, slug: "guide", content_type: "technical_article" as const, title: "راهنما", title_fa: "راهنما", title_en: "Guide", excerpt: "خلاصه", excerpt_fa: "خلاصه", excerpt_en: "Summary", featured_image: null, published_at: "2026-08-14T08:00:00Z", is_featured: false, category: null, related_products: [], related_catalog_categories: [], related_brands: [], related_industries: [], related_capabilities: [] };

describe("unified search UI", () => {
  it("uses semantic theme-safe tokens for every search surface", () => {
    const css = fs.readFileSync(path.resolve(process.cwd(), "app/globals.css"), "utf8");
    expect(css).toContain("--search-surface:var(--color-surface)");
    expect(css).toContain(".site-search-links a{display:grid;gap:4px;padding:11px 13px;border:1px solid var(--search-border);color:var(--search-text);background:var(--search-surface)}");
    expect(css).toContain(".site-search-group-summary a{display:inline-flex;align-items:center;gap:7px;white-space:nowrap;border:1px solid var(--search-border)");
    expect(css).toContain(".reference-primary-links>a[aria-current=\"page\"]");
  });

  it("renders grouped results and cross-links", () => {
    render(<><SearchProductGroup products={[product]} locale="fa" query="چیلر" /><SearchCategoryGroup categories={[{ id: 1, slug: "hvac", name: "تهویه", name_fa: "تهویه", name_en: "HVAC", image: null, product_count: 2 }]} locale="fa" /><SearchEditorialGroup articles={[article]} locale="fa" /></>);
    expect(screen.getByRole("heading", { name: "محصولات" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /مشاهده همه محصولات/ })).toHaveAttribute("href", "/fa/shop?q=%DA%86%DB%8C%D9%84%D8%B1");
    expect(screen.getByRole("link", { name: /تهویه/ })).toHaveAttribute("href", "/fa/category/hvac");
    expect(screen.getByRole("link", { name: /راهنما/ })).toHaveAttribute("href", "/fa/knowledge/guide");
  });

  it("omits empty groups and keeps the search form shareable", () => {
    render(<><SearchProductGroup products={[]} locale="en" query="" /><SearchCategoryGroup categories={[]} locale="en" /><SearchEntryForm locale="en" query="chiller" /></>);
    expect(screen.queryByRole("heading", { name: "Products" })).not.toBeInTheDocument();
    expect(screen.getByRole("textbox")).toHaveValue("chiller");
    expect(screen.getByLabelText("Search products, categories, brands and knowledge").closest("form")).toHaveAttribute("action", "/en/search");
  });

  it("renders compact group navigation only when multiple groups exist", () => {
    render(<SearchGroupSummary groups={{ products: [product], categories: [], brands: [], articles: [article], faqs: [] }} locale="en" />);
    expect(screen.getByRole("navigation", { name: "Search result groups" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Products/ })).toHaveAttribute("href", "#search-products");
    expect(screen.getByRole("link", { name: /Knowledge & News/ })).toHaveAttribute("href", "#search-articles");
  });
});
