import fs from "node:fs";
import path from "node:path";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EditorialCard, EditorialContextSections, EditorialTypeNav, isDemoArticle, localizedText, typeLabel } from "../components/content/editorial";
import { ArticleDiscovery } from "../components/content/discovery";
import type { EditorialArticle } from "../types/api";

const article: EditorialArticle = {
  id: 1, slug: "demo-article", content_type: "technical_article", content_type_label: "مقاله فنی", title: "fallback", title_fa: "عنوان فارسی", title_en: "", excerpt: "خلاصه fallback", excerpt_fa: "خلاصه فارسی", excerpt_en: "", body: "متن", body_fa: "متن فارسی", body_en: "", featured_image: null, published_at: "2026-08-14T08:00:00Z", is_featured: true, category: { id: 1, slug: "technical", name_fa: "فنی", name_en: "Technical" }, related_products: [{ id: 2, code: "P-2", name: "محصول", slug: "product" }], related_catalog_categories: [], related_brands: [{ id: 3, name: "برند", slug: "brand" }], related_industries: [], related_capabilities: [], seo_title_fa: "SEO", seo_title_en: "", seo_description_fa: "SEO description", seo_description_en: "",
};
const read = (file: string) => fs.readFileSync(path.resolve(process.cwd(), file), "utf8");

describe("editorial frontend foundation", () => {
  it("uses Persian/English fallback without fabricating translation", () => {
    expect(localizedText(article, "fa", "title")).toBe("عنوان فارسی");
    expect(localizedText(article, "en", "title")).toBe("عنوان فارسی");
    expect(localizedText(article, "en", "excerpt")).toBe("خلاصه فارسی");
  });

  it("maps CMS content types to bilingual labels", () => {
    expect(typeLabel(article, "fa")).toBe("مقالات فنی");
    expect(typeLabel(article, "en")).toBe("Technical Articles");
  });

  it("identifies demo content for internal ordering without changing CMS data", () => {
    expect(isDemoArticle({ ...article, title_fa: "[DEMO] عنوان فارسی" })).toBe(true);
    expect(isDemoArticle(article)).toBe(false);
  });

  it("renders a readable card and URL-addressable type filters", () => {
    render(<><EditorialCard article={article} locale="fa" /><EditorialTypeNav locale="fa" basePath="/fa/knowledge" selectedType="technical_article" /></>);
    expect(screen.getByRole("link", { name: /عنوان فارسی/ })).toHaveAttribute("href", "/fa/knowledge/demo-article");
    expect(screen.getByRole("link", { name: "مقالات فنی" })).toHaveAttribute("href", "/fa/knowledge?type=technical_article");
    expect(screen.getByText("مطالعه مطلب")).toBeInTheDocument();
  });

  it("omits empty relationship sections and renders explicit commerce context", () => {
    render(<EditorialContextSections article={article} locale="fa" />);
    expect(screen.getByRole("heading", { name: "محصولات مرتبط" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "برندهای مرتبط" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "صنایع مرتبط" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "محصول" })).toHaveAttribute("href", "/fa/product/product");
  });

  it("renders bounded discovery groups without internal reason codes", () => {
    render(<ArticleDiscovery discovery={{ articles: [{ ...article, id: 5, slug: "related", related_products: [], related_brands: [] }], faqs: [], resources: [], products: [{ id: 7, slug: "other", code: "P-7", name_fa: "محصول دیگر", unit: "عدد", primary_image: null }] }} locale="fa" />);
    expect(screen.getByRole("heading", { name: "مطالب مرتبط" })).toBeInTheDocument();
    expect(screen.getAllByRole("heading", { name: "محصولات مرتبط" })).toHaveLength(2);
    expect(screen.queryByText("direct_product")).not.toBeInTheDocument();
  });

  it("keeps editorial routes server-rendered and metadata-aware", () => {
    const knowledge = read("app/[locale]/knowledge/page.tsx");
    const news = read("app/[locale]/news/page.tsx");
    const detail = read("app/[locale]/knowledge/[slug]/page.tsx");
    for (const source of [knowledge, news, detail]) {
      expect(source).toContain("localizedAlternates");
      expect(source).toContain("absoluteUrl(localizedPath(locale");
      expect(source).not.toContain("use client");
    }
    expect(detail).toContain("notFound()");
    expect(detail).toContain("TechArticle");
    expect(detail).not.toContain("dangerouslySetInnerHTML={{ __html: body");
  });
});
