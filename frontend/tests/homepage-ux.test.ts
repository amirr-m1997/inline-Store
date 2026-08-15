import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { localizeHeroLink } from "../components/catalog/site-hero";

const read = (file: string) => fs.readFileSync(path.resolve(process.cwd(), file), "utf8");

describe("homepage final UX safeguards", () => {
  it("keeps hero links locale-safe and promotes the first real hero action", () => {
    expect(localizeHeroLink("/fa/shop", "en")).toBe("/en/shop");
    expect(localizeHeroLink("/contact", "fa")).toBe("/contact");
    const source = read("components/catalog/site-hero.tsx");
    expect(source).toContain('index === 0 ? "primary" : "secondary"');
  });

  it("preserves one H1 and clean fallbacks for missing homepage data", () => {
    const source = read("components/catalog/enterprise-home.tsx");
    const hero = read("components/catalog/site-hero.tsx");
    expect(hero).toContain("<h1>{hero.title}</h1>");
    expect(source).toContain("دسته‌بندی‌های محصولات در دسترس نیست.");
    expect(source).toContain("home-section-empty");
  });

  it("keeps locale-safe product section links and accessible category labels", () => {
    const source = read("components/catalog/enterprise-home.tsx");
    expect(source).toContain("aria-label={`${title}؛ مشاهده همه`}");
    expect(source).toContain("aria-label={`مشاهده دسته ${category.name_fa}`}");
    expect(source).toContain("/${locale}/best-discounts");
  });
});
