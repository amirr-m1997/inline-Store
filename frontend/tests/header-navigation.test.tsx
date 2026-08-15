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
    const input = screen.getAllByRole("textbox", { name: /جست‌وجوی محصولات/ }).at(-1)!;
    fireEvent.change(input, { target: { value: "bearing" } });
    expect(screen.getByRole("button", { name: "پاک کردن جست‌وجو" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "جست‌وجو" }));
    expect(push).toHaveBeenCalledWith("/en/search?q=bearing");
    expect(push).not.toHaveBeenCalledWith(expect.stringContaining("/category/search"));
    fireEvent.click(screen.getByRole("button", { name: "پاک کردن جست‌وجو" }));
    expect(input).toHaveValue("");
    expect(push).toHaveBeenCalledTimes(1);
  });

  it("keeps long RTL/LTR queries inside a reserved control contract", () => {
    render(<SearchBar />);
    const input = screen.getAllByRole("textbox", { name: /جست‌وجوی محصولات/ }).at(-1)!;
    fireEvent.change(input, { target: { value: "[DEMO] تجهیزات فنی برای انتخاب و نگهداری سامانه صنعتی" } });
    expect(input).toHaveAttribute("dir", "ltr");
    expect(input).toHaveClass("reference-search-input");
    expect(screen.getByRole("button", { name: "پاک کردن جست‌وجو" })).toHaveAttribute("type", "button");
    fireEvent.click(screen.getByRole("button", { name: "پاک کردن جست‌وجو" }));
    expect(push).not.toHaveBeenCalled();
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
    expect(source).toContain("/${locale}/rfq");
    expect(source).toContain("استعلام قیمت");
    expect(source).toContain("Request a Quote");
    expect(source).toContain("aria-current");
  });

  it("keeps the Product Categories trigger readable before activation", () => {
    const css = fs.readFileSync(path.resolve(process.cwd(), "app/globals.css"), "utf8");
    expect(css).toContain(".category-menu-trigger:hover");
    expect(css).toContain(".category-menu-trigger:hover b");
    expect(css).toContain("color:#fff!important");
    expect(css).toContain("html.dark .reference-primary-links>a:hover");
    expect(css).toContain("color:var(--color-text-primary)!important");
  });

  it("does not probe the private profile endpoint on anonymous header mount", () => {
    const source = fs.readFileSync(path.resolve(process.cwd(), "components/layout/site-header.tsx"), "utf8");
    expect(source).not.toContain("void load(); window.addEventListener(\"auth-changed\", load)");
    expect(source).toContain('event.detail?.authenticated === true');
    expect(source).toContain('new CustomEvent("auth-changed", { detail: { authenticated: false } })');
  });
});
