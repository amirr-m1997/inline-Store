import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FAQList } from "../components/content/editorial";
import { SearchFAQGroup } from "../components/search/search-results";
import type { FAQEntry } from "../types/api";

const faq: FAQEntry = { id: 1, slug: "demo-faq", faq_type: "technical", question: "پرسش", question_fa: "پرسش فنی", question_en: "Technical question", answer: "پاسخ", answer_fa: "پاسخ فنی", answer_en: "Technical answer", display_order: 1, related_products: [{ id: 1, code: "P-1", name: "Product", slug: "product" }], related_categories: [], related_industries: [], related_capabilities: [], related_articles: [] };

describe("FAQ discovery", () => {
  it("renders localized native disclosure and contextual links", () => {
    render(<FAQList faqs={[faq]} locale="fa" title="سوالات متداول" />);
    expect(screen.getByText("پرسش فنی")).toBeInTheDocument();
    expect(screen.getByText("پاسخ فنی")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Product" })).toHaveAttribute("href", "/fa/product/product");
  });

  it("renders FAQ results in the unified search group", () => {
    render(<SearchFAQGroup faqs={[faq]} locale="en" />);
    expect(screen.getByRole("heading", { name: "Frequently Asked Questions" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Technical question" })).toHaveAttribute("href", "/en/faq#faq-demo-faq");
  });
});
