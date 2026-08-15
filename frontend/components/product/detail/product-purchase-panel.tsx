"use client";
import { useState } from "react";
import type { ProductDetail, ProductVariant, VariantSelection } from "../../../lib/product/types";
import { VariantSelector } from "./variant-selector";

export function ProductPurchasePanel({ product, onVariantChange, onSelectionChange }: { product: ProductDetail; onVariantChange?: (variant?: ProductVariant) => void; onSelectionChange?: (selection: VariantSelection) => void }) {
  const [variant, setVariant] = useState<ProductVariant | undefined>();
  const select = (selection: VariantSelection) => { setVariant(selection.resolvedVariant); onVariantChange?.(selection.resolvedVariant); onSelectionChange?.(selection); };
  const pricing = variant?.pricing || product.pricing;
  const discount = Number(pricing?.discountPercentage ?? 0) > 0 ? pricing?.discountPercentage : undefined;
  return <><VariantSelector product={product} onChange={select} /><div className="product-price-panel">{discount && <span className="product-detail-discount">٪{Number(discount).toLocaleString("fa-IR")} تخفیف</span>}{pricing?.finalAmount ? <>{discount && pricing.originalAmount && <del>{Number(pricing.originalAmount).toLocaleString("fa-IR")} ریال</del>}<strong>{Number(pricing.finalAmount).toLocaleString("fa-IR")} <small>ریال</small></strong></> : <p>{product.purchaseMode === "quote" ? "نیازمند استعلام قیمت" : "قیمت برای این محصول ثبت نشده است."}</p>}</div></>;
}
