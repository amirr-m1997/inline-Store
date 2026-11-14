import { render, screen, within } from "@testing-library/react";
import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { CartSummary } from "../components/cart/cart-summary";
import { CheckoutProgress } from "../components/cart/checkout-progress";

describe("cart and checkout UX", () => {
  it("keeps item mutations and checkout errors accessible", () => {
    const source = fs.readFileSync(path.resolve(process.cwd(), "app/[locale]/cart/page.tsx"), "utf8");
    expect(source).toContain("aria-label={`کاهش تعداد ${item.product.name}`}");
    expect(source).toContain("aria-label={`حذف ${item.product.name} از سبد`}");
    expect(source).toContain("<details className=\"cart-discount-box\">");
    expect(source).toContain("className=\"checkout-primary-action");
    expect(source).toContain("role=\"alert\"");
    expect(source).toContain("/rfq?source=cart");
    expect(source).toContain("استعلام قیمت اقلام سبد");
  });

  it("exposes the real cart, order details, and payment progression", () => {
    render(<CheckoutProgress hasItems customerComplete={false} />);
    expect(screen.getByRole("navigation", { name: "مراحل ثبت سفارش" })).toBeInTheDocument();
    expect(screen.getByText("سبد خرید")).toBeInTheDocument();
    expect(screen.getByText("اطلاعات سفارش")).toBeInTheDocument();
    expect(screen.getByText("پرداخت")).toBeInTheDocument();
    expect(screen.getByText("انتقال به درگاه پرداخت")).toBeInTheDocument();
    expect(document.querySelector(".checkout-progress li.is-current")).toHaveTextContent("سبد خرید");
  });

  it("distinguishes subtotal, discount, and payable total without inventing shipping", () => {
    render(<CartSummary cart={{ subtotal: "1000", discount_amount: "100", total: "900" } as never} />);
    expect(screen.getByText("جمع کالاها")).toBeInTheDocument();
    expect(screen.getByText("تخفیف")).toBeInTheDocument();
    expect(screen.getByText("مبلغ قابل پرداخت")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "خلاصه سفارش" }).closest("section")).not.toHaveTextContent("هزینه ارسال");
  });

  it("does not present an unpriced cart as a zero-value payable order", () => {
    const view = render(<CartSummary cart={{ subtotal: "0", discount_amount: "0", total: "0", unpriced_items_count: 1, checkout_eligible: false }} />);
    expect(within(view.container).getByText("نیازمند استعلام قیمت")).toBeInTheDocument();
    expect(within(view.container).queryByText("مبلغ قابل پرداخت")).not.toBeInTheDocument();
  });
});
