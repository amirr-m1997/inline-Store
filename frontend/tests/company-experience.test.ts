import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const read = (file: string) => fs.readFileSync(path.resolve(process.cwd(), file), "utf8");

describe("Mehrasl company experience", () => {
  it("composes About from published server data and omits empty sections", () => {
    const source = read("app/[locale]/about/page.tsx");
    expect(source).toContain("getCompanyMilestonesServer");
    expect(source).toContain("getCompanyLocationsServer");
    expect(source).toContain("getCompanyCertificationsServer");
    expect(source).toContain("<CompanyTimeline milestones={milestones}");
    expect(source).toContain("capabilities.length > 0");
    expect(source).toContain("<CompanyCertificationCards items={certifications}");
    expect(source).not.toContain("useEffect");
    expect(source).toContain("locations.slice(0, 3)");
    expect(source).toContain("showHeader={false} compact");
    expect(source).toContain("capabilities.slice(0, 3)");
    expect(source).toContain("View all locations");
  });

  it("keeps mobile navigation and location previews deliberately compact", () => {
    const navigation = read("components/layout/category-navigation.tsx");
    const locations = read("components/content/company-location-groups.tsx");
    expect(navigation).toContain("reference-primary-links");
    expect(navigation).toContain("mobile-nav-section-label");
    expect(navigation).toContain("بازگشت به سطح قبل");
    expect(navigation).toContain('mobileMode === "main"');
    expect(navigation).toContain("returnToMainMenu");
    expect(locations).toContain("showHeader = true");
    expect(locations).toContain("company-locations--compact");
  });

  it("keeps homepage company sections as bounded previews and marks demo content", () => {
    const source = read("components/catalog/enterprise-home.tsx");
    expect(source).toContain("industries.slice(0, 4)");
    expect(source).toContain("capabilities.slice(0, 3)");
    expect(source).toContain("content-demo-indicator");
    expect(source.indexOf("Featured products")).toBeLessThan(source.indexOf("Industries and applications"));
  });

  it("omits invalid demo capability destinations", () => {
    const source = read("app/[locale]/capabilities/[slug]/page.tsx");
    expect(source).toContain("item.cta_url !== \"/demo-content\"");
    expect(source).toContain("validCta");
  });

  it("keeps location and industry indexes noindexable when no published records exist", () => {
    const locations = read("app/[locale]/locations/page.tsx");
    const industries = read("app/[locale]/industries/page.tsx");
    for (const source of [locations, industries]) {
      expect(source).toContain("index: false");
      expect(source).toContain("localizedAlternates");
      expect(source).toContain("No published");
    }
  });

  it("uses the implemented locale-safe Customer Service destinations", () => {
    const source = read("app/[locale]/support/page.tsx");
    expect(source).toContain("/${locale}/support/${path}");
    expect(source).toContain("/${locale}/account/orders");
    expect(source).not.toContain("`/${locale}/${path}`");
  });

  it("renders only real relationship arrays on industry detail", () => {
    const source = read("app/[locale]/industries/[slug]/page.tsx");
    expect(source).toContain("item.capabilities.length > 0");
    expect(source).toContain("item.categories.length > 0");
    expect(source).toContain("item.products.length > 0");
    expect(source).toContain("/capabilities/${capability.slug}");
  });
});
