import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const read = (file: string) => fs.readFileSync(path.resolve(process.cwd(), file), "utf8");

describe("SSR request regression guards", () => {
  it("hydrates catalog from initial data before enabling client requests", () => {
    const source = read("components/catalog/catalog-explorer.tsx");
    expect(source).toContain("initialConsumed = useRef(!initialData)");
    expect(source).toContain("if (!initialConsumed.current) { initialConsumed.current = true; return; }");
  });
  it("loads homepage content through one server data loader", () => {
    const source = read("app/[locale]/page.tsx");
    expect(source).toContain("loadHomepageData");
    expect(source).toContain("getHomepageCompany = cache");
    expect(source).not.toContain("useEffect");
  });
  it("keeps PDP data loading in the server route", () => {
    const route = read("app/[locale]/product/[slug]/page.tsx");
    expect(route).toContain("getProductServer");
    expect(route).not.toContain("getProduct(");
    expect(route).toContain("ProductDetailInteractive");
  });
});
