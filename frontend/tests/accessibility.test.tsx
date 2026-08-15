import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { axe } from "vitest-axe";
import { Drawer } from "../components/ui/drawer";
import { Dialog } from "../components/ui/dialog";
import { SearchBox } from "../components/catalog/search-box";
import { VariantSelector } from "../components/product/detail/variant-selector";
import { ProductTabs } from "../components/product/detail/product-tabs";
import type { ProductDetail } from "../lib/product/types";

const product = { id: 1, name: "محصول", slug: "p", code: "P", unit: "عدد", media: [], availability: { quantity: 1, availableToCart: 1 }, categories: [], specifications: [], variants: [{ id: "v1", sku: "V1", attributes: [{ name: "رنگ", value: "قرمز" }] }], serviceAdvantages: [], relationships: [], documents: [] } as ProductDetail;

describe("storefront accessibility", () => {
  it.each([
    ["search", () => <SearchBox onSearch={() => undefined} />],
    ["variants", () => <VariantSelector product={product} />],
    ["tabs", () => <ProductTabs description="توضیحات" specifications={<p>مشخصات</p>} />],
    ["dialog", () => <Dialog open onClose={() => undefined} title="نمونه"><button type="button">اقدام</button></Dialog>],
    ["drawer", () => <Drawer open onClose={() => undefined} title="نمونه"><button type="button">اقدام</button></Drawer>],
  ])("has no automated accessibility violations: %s", async (_name, component) => {
    const { container } = render(component());
    const results = await axe(container);
    (expect(results) as unknown as { toHaveNoViolations: () => void }).toHaveNoViolations();
  });
});
