import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const read = (file: string) => fs.readFileSync(path.resolve(process.cwd(), file), "utf8");

describe("customer quotation UI contract", () => {
  it("uses private localized quotation metadata and safe API fields", () => {
    const page = read("app/[locale]/account/quotations/[reference]/page.tsx");
    const component = read("components/account/account-quotation.tsx");
    expect(page).toContain("index: false");
    expect(page).toContain("follow: false");
    expect(component).toContain("quotation.reference");
    expect(component).toContain("quotation.rfq_reference");
    expect(component).toContain("دانلود PDF پیشنهاد قیمت");
    expect(component).toContain("/pdf/?locale=");
    expect(component).not.toContain("internal_notes");
    expect(component).toContain("Accept Quotation");
    expect(component).toContain("Request Revision");
    expect(component).toContain("Reject Quotation");
    expect(component).toContain("does not automatically create an order or payment");
    expect(component).not.toContain("Pay");
    expect(component).not.toContain("Pay");
  });

  it("keeps monetary identifiers and quotation rows LTR-safe", () => {
    const component = read("components/account/account-quotation.tsx");
    expect(component).toContain('dir="ltr"');
    expect(component).toContain("unit_price");
    expect(component).toContain("line_total");
    expect(component).toContain("quotation.subtotal");
  });

  it("keeps customer responses explicit, bounded, and one-shot", () => {
    const component = read("components/account/account-quotation.tsx");
    expect(component).toContain("role=\"dialog\"");
    expect(component).toContain("role=\"status\"");
    expect(component).toContain("maxLength={2000}");
    expect(component).toContain("revision_requested");
    expect(component).toContain("currentResponse === \"pending\"");
  });
});
