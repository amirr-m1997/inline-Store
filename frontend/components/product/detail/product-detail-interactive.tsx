"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import { addItem } from "../../../lib/api/cart";
import type { ProductDetail as ApiProductDetail } from "../../../lib/api/products";
import type { ProductDetail as DomainProductDetail, ProductVariant, VariantSelection } from "../../../lib/product/types";
import { ProductPurchasePanel } from "./product-purchase-panel";
import { ProductGallery } from "./product-gallery";

const faNumber = (value: number | null) => value === null ? "ثبت نشده" : value.toLocaleString("fa-IR");
const parseFaInteger = (value: string) => Number(value.replace(/[۰-۹]/g, (digit) => String("۰۱۲۳۴۵۶۷۸۹".indexOf(digit))).replace(/\D/g, ""));
export function getMissingVariantAttributes(variants: ProductVariant[], selected: Record<string, string>) { return Array.from(new Set(variants.flatMap((variant) => variant.attributes.map((attribute) => attribute.name)))).filter((name) => !selected[name]); }
export function getPurchaseCtaState(hasVariants: boolean, hasSelection: boolean, available: number, adding: boolean, selectionComplete = false) { if (adding) return "loading"; if (hasVariants && !hasSelection) return selectionComplete ? "unavailable" : "selection_required"; if (available < 1) return "unavailable"; return "ready"; }
export function clampPurchaseQuantity(next: number, max: number) { return max > 0 ? Math.min(max, Math.max(1, Number.isFinite(next) ? next : 1)) : 0; }

export function ProductDetailInteractive({ product, domainProduct, identity }: { product: ApiProductDetail; domainProduct: DomainProductDetail; identity: ReactNode }) {
  const [quantity, setQuantity] = useState(product.inventory.allowed_for_cart > 0 ? 1 : 0);
  const [adding, setAdding] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [selectedVariant, setSelectedVariant] = useState<ProductVariant | undefined>();
  const [selectedAttributes, setSelectedAttributes] = useState<Record<string, string>>({});
  const hasVariants = domainProduct.variants.length > 0;
  const missingAttributes = getMissingVariantAttributes(domainProduct.variants, selectedAttributes);
  const maxQuantity = hasVariants && !selectedVariant ? 0 : selectedVariant?.availability?.availableToCart ?? product.inventory.allowed_for_cart ?? 0;
  const changeQuantity = (next: number) => { setFeedback(null); setQuantity(clampPurchaseQuantity(next, maxQuantity)); };
  const addToCart = async () => {
    if (quantity < 1 || adding) return;
    setAdding(true); setFeedback(null);
    try { await addItem(product.id, quantity); window.dispatchEvent(new Event("cart-updated")); setFeedback({ type: "success", text: "محصول با موفقیت به سبد خرید افزوده شد." }); }
    catch (reason) { setFeedback({ type: "error", text: reason instanceof Error ? reason.message : "افزودن به سبد خرید ناموفق بود." }); }
    finally { setAdding(false); }
  };
  const onSelection = (selection: VariantSelection) => { setSelectedAttributes(selection.selected); setSelectedVariant(selection.resolvedVariant); setFeedback(null); setQuantity(selection.resolvedVariant?.availability?.availableToCart ? 1 : 0); };
  const ctaState = getPurchaseCtaState(hasVariants, Boolean(selectedVariant), maxQuantity, adding, missingAttributes.length === 0);
  const ctaLabel = feedback?.type === "success" && !adding ? "به سبد خرید افزوده شد" : ctaState === "loading" ? "در حال افزودن…" : ctaState === "selection_required" ? "انتخاب مشخصات برای ادامه" : ctaState === "unavailable" ? "ناموجود" : "افزودن به سبد خرید";
  const ctaReason = hasVariants && !selectedVariant ? (missingAttributes.length ? `برای خرید، ${missingAttributes.join("، ")} را انتخاب کنید.` : "ترکیب انتخاب‌شده در دسترس نیست.") : maxQuantity < 1 ? "این محصول در حال حاضر قابل سفارش نیست." : "";
  const selectedSummary = selectedVariant ? selectedVariant.attributes.map((attribute) => `${attribute.name}: ${attribute.value}`).join("، ") : "";
  return <>
    <aside className="product-buy-panel">{identity}
      {hasVariants && !selectedVariant && <p id="variant-guidance" className="variant-guidance" role="status" aria-live="polite"><b>{missingAttributes.length ? "انتخاب مشخصات الزامی است" : "ترکیب در دسترس نیست"}</b><span>{ctaReason}</span></p>}
      {selectedVariant && <div className="variant-selection-summary" role="status" aria-live="polite"><b>پیکربندی انتخاب‌شده</b><span>{selectedSummary}</span>{selectedVariant.sku && <small dir="ltr">SKU: {selectedVariant.sku}</small>}</div>}
      <div className={`product-stock-row ${maxQuantity > 0 ? "available" : "unavailable"}`} role="status" aria-live="polite"><i aria-hidden="true" /> <strong>{maxQuantity > 0 ? "موجود" : "ناموجود"}</strong>{maxQuantity > 0 && <span>موجودی: {faNumber(maxQuantity)} {product.unit}</span>}</div>
      <ProductPurchasePanel product={domainProduct} onVariantChange={setSelectedVariant} onSelectionChange={onSelection} />
      <div className="product-cart-actions"><label htmlFor="product-quantity">تعداد</label><div className="quantity-control" aria-label="کنترل تعداد"><button type="button" onClick={() => changeQuantity(quantity - 1)} disabled={quantity <= 1 || adding || maxQuantity < 1} aria-label="کاهش تعداد">−</button><input id="product-quantity" value={quantity.toLocaleString("fa-IR")} onChange={(event) => changeQuantity(parseFaInteger(event.target.value))} inputMode="numeric" min={maxQuantity > 0 ? 1 : undefined} max={maxQuantity > 0 ? maxQuantity : undefined} aria-describedby="quantity-help" disabled={adding || maxQuantity < 1} /><button type="button" onClick={() => changeQuantity(quantity + 1)} disabled={quantity >= maxQuantity || adding || maxQuantity < 1} aria-label="افزایش تعداد">+</button></div><small id="quantity-help" className="quantity-help">{maxQuantity > 0 ? `حداکثر ${faNumber(maxQuantity)} ${product.unit}` : ctaReason}</small><button className={`add-cart-button ${feedback?.type === "success" ? "is-success" : ""}`} type="button" onClick={addToCart} disabled={quantity < 1 || maxQuantity < 1 || adding} aria-describedby={hasVariants && !selectedVariant ? "variant-guidance" : "quantity-help"}>{ctaLabel}</button>{feedback && <p className={`cart-feedback ${feedback.type === "error" ? "is-error" : "is-success"}`} role={feedback.type === "error" ? "alert" : "status"} aria-live="polite">{feedback.text}</p>}</div>
      {product.service_advantages.length > 0 && <div className="product-services" aria-label="خدمات خرید">{product.service_advantages.map((advantage) => <article key={advantage.id}><i aria-hidden="true">{advantage.icon || "✓"}</i><div><b>{advantage.title_fa}</b>{advantage.description_fa && <small>{advantage.description_fa}</small>}</div></article>)}</div>}
    </aside>
    <ProductGallery product={domainProduct} />
  </>;
}
