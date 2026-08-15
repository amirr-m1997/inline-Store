import { describe, expect, it } from "vitest";
import robots from "../app/robots";
import { catalogMetadata, catalogStructuredData } from "../lib/catalog-server";
import { absoluteUrl, localizedAlternates } from "../lib/locale-url";

describe("SEO and locale hardening", () => {
  it("publishes locale alternates and absolute canonical URLs", () => {
    const metadata = catalogMetadata("shop", "en", null, {});
    expect(metadata.alternates?.canonical).toBe(absoluteUrl("/en/shop"));
    expect(metadata.alternates?.languages).toEqual(localizedAlternates("/shop").languages);
  });

  it("noindexes filtered catalog states while allowing crawlers to follow", () => {
    expect(catalogMetadata("shop", "fa", null, { q: "bearing" }).robots).toEqual({ index: false, follow: true });
    expect(catalogMetadata("shop", "fa", null, {}).robots).toEqual({ index: true, follow: true });
  });

  it("emits absolute structured-data links", () => {
    const data = catalogStructuredData("shop", "fa", null, { products: [{ id: 1, name: "Test", slug: "test", code: "T", unit: "ea", available_quantity: 1, category: null, images: [], price: null }], facets: [], applied_filters: {}, next_cursor: null, previous_cursor: null, has_more: false, total_count: 1 });
    expect(JSON.stringify(data)).toContain(absoluteUrl("/fa/product/test"));
    expect(JSON.stringify(data)).toContain(absoluteUrl("/fa"));
  });

  it("disallows private and operational routes in robots output", () => {
    const output = robots();
    const rule = Array.isArray(output.rules) ? output.rules[0] : output.rules;
    expect(rule.disallow).toEqual(expect.arrayContaining(["/api/", "/fa/account", "/en/account", "/fa/cart", "/en/payment"]));
    expect(output.sitemap).toBe(absoluteUrl("/sitemap.xml"));
  });
});
