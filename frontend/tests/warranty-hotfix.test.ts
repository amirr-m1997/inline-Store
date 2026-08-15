import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const read = (file: string) => fs.readFileSync(path.resolve(process.cwd(), file), "utf8");

describe("Phase 10.9A warranty and support-request visual hotfix", () => {
  it("keeps warranty registration discoverable without policy content", () => {
    const page = read("app/[locale]/support/warranty/page.tsx");
    expect(page).toContain("warranty-registration-section");
    expect(page).toContain("WarrantyRegistrationForm");
    expect(page).toContain("Additional warranty terms will be published here after company approval.");
    expect(page).toContain("اطلاعات تکمیلی شرایط گارانتی پس از تأیید شرکت در این بخش منتشر می‌شود.");
    expect(page).not.toContain("warranty activated");
    expect(page).not.toContain("warranty approved");
  });

  it("adds the customer-service request introduction and bounded form layout", () => {
    const page = read("app/[locale]/support/request/page.tsx");
    const styles = read("app/globals.css");
    expect(page).toContain("support-request-page");
    expect(page).toContain("ثبت درخواست پشتیبانی");
    expect(page).toContain("Submit a support request");
    expect(styles).toContain(".support-request-stack>.contact-form");
    expect(styles).toContain("grid-template-columns:repeat(2,minmax(0,1fr))");
    expect(styles).toContain("@media(max-width:767px)");
  });
});
