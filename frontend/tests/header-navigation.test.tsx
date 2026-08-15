import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { push, getCart } = vi.hoisted(() => ({ push: vi.fn(), getCart: vi.fn() }));

vi.mock("next/navigation", () => ({ useParams: () => ({ locale: "en" }), useRouter: () => ({ push }) }));
vi.mock("../lib/api/cart", () => ({ getCart }));

import { SearchBar } from "../components/layout/search-bar";
import { CartButton } from "../components/layout/cart-button";
import fs from "node:fs";
import path from "node:path";

describe("header navigation controls", () => {
  beforeEach(() => { push.mockReset(); getCart.mockReset(); getCart.mockResolvedValue({ items: [{ quantity: 2 }] }); });

  it("exposes a labeled search and clear control without changing submit behavior", () => {
    render(<SearchBar />);
    const input = screen.getByRole("textbox", { name: /جست‌وجوی محصولات/ });
    fireEvent.change(input, { target: { value: "bearing" } });
    expect(screen.getByRole("button", { name: "پاک کردن جست‌وجو" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "جست‌وجو" }));
    expect(push).toHaveBeenCalledWith("/en/shop?q=bearing");
    expect(push).not.toHaveBeenCalledWith(expect.stringContaining("/category/search"));
    fireEvent.click(screen.getByRole("button", { name: "پاک کردن جست‌وجو" }));
    expect(input).toHaveValue("");
  });

  it("keeps cart count understandable and locale-safe", async () => {
    render(<CartButton locale="en" />);
    await waitFor(() => expect(screen.getByRole("link", { name: /سبد خرید، 2 کالا/ })).toBeInTheDocument());
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("includes the locale-safe Customer Service hub in primary/mobile navigation", () => {
    const source = fs.readFileSync(path.resolve(process.cwd(), "components/layout/category-navigation.tsx"), "utf8");
    expect(source).toContain("/${locale}/support");
    expect(source).toContain("امور مشتریان");
    expect(source).toContain("Customer Service");
    expect(source).toContain("aria-current");
  });
});
