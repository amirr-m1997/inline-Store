import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CatalogToolbar } from "../components/catalog/catalog-toolbar";
import { FacetGroup } from "../components/catalog/facet-group";
import { MobileFilterDrawer } from "../components/catalog/mobile-filter-drawer";
import { RangeFilter } from "../components/catalog/range-filter";
import type { CatalogFacet } from "../components/catalog/facet-types";

const facet: CatalogFacet = { name: "brand", label: "برند", type: "checkbox", options: Array.from({ length: 10 }, (_, index) => ({ value: String(index), label: `برند ${index}`, count: index + 1 })) };

describe("mobile catalog controls", () => {
  it("exposes result count and active filter count on the filter trigger", () => {
    render(<CatalogToolbar query="پیچ" ordering="code" inStock resultCount={24} searchLoading={false} activeFilterCount={3} onSearch={vi.fn()} onOrderingChange={vi.fn()} onStockChange={vi.fn()} onOpenFilters={vi.fn()} />);
    expect(screen.getByRole("button", { name: /۳ فیلتر فعال/ })).toBeInTheDocument();
    const sortTrigger = screen.getByRole("button", { name: "مرتب‌سازی" });
    expect(sortTrigger).toBeInTheDocument();
    expect(sortTrigger).toHaveAttribute("aria-haspopup", "listbox");
    expect(screen.getByRole("checkbox", { name: "فقط موجود", checked: true })).toBeInTheDocument();
  });

  it("expands long facet groups without changing their options", () => {
    render(<FacetGroup facet={facet} onOptionChange={vi.fn()} />);
    expect(screen.getByText("برند 7")).toBeInTheDocument();
    expect(screen.queryByText("برند 8")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /نمایش/ }));
    expect(screen.getByText("برند 9")).toBeInTheDocument();
  });

  it("provides explicit reset/apply actions and result context in the drawer", () => {
    render(<MobileFilterDrawer open ordering="code" inStock={false} resultCount={24} activeFilterCount={2} facets={[facet]} onClose={vi.fn()} onApply={vi.fn()} onReset={vi.fn()} />);
    expect(screen.getByRole("dialog")).toHaveAccessibleName("فیلترهای کاتالوگ (۲ فعال)");
    expect(screen.getByText("۲۴ محصول با این فیلترها")).toBeInTheDocument();
    const drawerSortTrigger = within(screen.getByRole("dialog")).getByRole("button", { name: "مرتب‌سازی" });
    expect(drawerSortTrigger).toBeInTheDocument();
    expect(drawerSortTrigger).toHaveAttribute("aria-haspopup", "listbox");
    expect(screen.getByRole("button", { name: "پاک‌سازی فیلترها" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /نمایش نتایج/ })).toBeInTheDocument();
  });

  it("keeps range units attached to accessible min/max fields", () => {
    render(<RangeFilter facet={{ name: "ولتاژ", min: 380, max: 480, unit: "V" }} />);
    expect(screen.getByRole("textbox", { name: "ولتاژ از" })).toHaveAccessibleName("ولتاژ از");
    expect(screen.getByRole("textbox", { name: "ولتاژ تا" })).toHaveAccessibleName("ولتاژ تا");
    expect(screen.getAllByText("V")).toHaveLength(2);
  });

  it("debounces range changes until typing pauses", () => {
    vi.useFakeTimers();
    const onChange = vi.fn();
    render(<RangeFilter facet={{ name: "قیمت", unit: "ریال" }} onChange={onChange} />);
    fireEvent.change(screen.getByRole("textbox", { name: "قیمت از" }), { target: { value: "1" } });
    fireEvent.change(screen.getByRole("textbox", { name: "قیمت از" }), { target: { value: "10" } });
    expect(onChange).not.toHaveBeenCalled();
    vi.advanceTimersByTime(449);
    expect(onChange).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenLastCalledWith({ min: "10", max: undefined });
    vi.useRealTimers();
  });

  it("renders the stock filter as a compact accessible checkbox and supports price bounds", () => {
    render(<MobileFilterDrawer open ordering="code" inStock={false} resultCount={24} facets={[{ name: "price", label: "قیمت", type: "range", min: 1000, max: 9000, unit: "ریال" }]} onClose={vi.fn()} onApply={vi.fn()} />);
    const drawer = screen.getAllByRole("dialog").at(-1)!;
    expect(within(drawer).getByRole("checkbox", { name: "فقط موجود" })).toBeInTheDocument();
    expect(within(drawer).getByRole("textbox", { name: "قیمت از" })).toBeInTheDocument();
    expect(within(drawer).getByRole("textbox", { name: "قیمت تا" })).toBeInTheDocument();
    expect(within(drawer).getAllByText("ریال")).toHaveLength(2);
  });
});
