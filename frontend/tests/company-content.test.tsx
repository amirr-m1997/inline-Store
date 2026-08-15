import fs from "node:fs";
import path from "node:path";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ContactForm } from "../components/content/contact-form";

vi.mock("../lib/api/content", () => ({ sendContact: vi.fn() }));
const read = (file: string) => fs.readFileSync(path.resolve(process.cwd(), file), "utf8");

describe("existing-data company content", () => {
  it("loads About company and advantages on the server without a client fetch", () => {
    const source = read("app/[locale]/about/page.tsx");
    expect(source).toContain("getCompanyServer<CompanyInfo>()");
    expect(source).toContain("getAdvantagesServer<Advantage[]>()");
    expect(source).not.toContain("useEffect");
    expect(source).toContain("company?.description");
    expect(source).toContain("company?.logo");
  });

  it("omits optional contact values instead of rendering empty placeholders", () => {
    const source = read("app/[locale]/contact/page.tsx");
    expect(source).toContain("company?.phone ?");
    expect(source).toContain("company?.address ?");
    expect(source).toContain("company?.working_hours ?");
    expect(source).not.toContain("نقشه پس از ثبت");
  });

  it("provides explicit accessible contact form labels and status behavior", () => {
    render(<ContactForm />);
    expect(screen.getByLabelText("شماره تماس *")).toBeInTheDocument();
    expect(screen.getByLabelText("ایمیل")).toBeInTheDocument();
    expect(screen.getByLabelText("موضوع *")).toBeInTheDocument();
    expect(screen.getByLabelText("پیام *")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ثبت پیام" })).toBeInTheDocument();
  });

  it("keeps About and Contact metadata locale-aware and links contextual CTAs", () => {
    const about = read("app/[locale]/about/page.tsx");
    const contact = read("app/[locale]/contact/page.tsx");
    const homepage = read("components/catalog/enterprise-home.tsx");
    for (const source of [about, contact]) {
      expect(source).toContain("localizedAlternates");
      expect(source).toContain("absoluteUrl(localizedPath(locale, path))");
    }
    expect(about).toContain("/${locale}/shop");
    expect(about).toContain("/${locale}/contact");
    expect(contact).toContain("/${locale}/shop");
    expect(homepage).toContain("/${locale}/about");
    expect(homepage).toContain("/${locale}/contact");
  });
});
