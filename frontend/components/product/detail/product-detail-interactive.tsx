"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import { addItem } from "../../../lib/api/cart";
import type { ProductDetail as ApiProductDetail } from "../../../lib/api/products";
import type { ProductDetail as DomainProductDetail, ProductVariant, VariantSelection } from "../../../lib/product/types";
import { formatNumber } from "../../../lib/product/formatters";
import { ProductPurchasePanel } from "./product-purchase-panel";
import { ProductGallery } from "./product-gallery";

const faNumber = (value: number | null) => value === null ? "ثبت نشده" : formatNumber(value);
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
  const [shareFeedback, setShareFeedback] = useState<string | null>(null);
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
  const shareSpecSheet = async () => {
    const specs = (product.technical_specifications || []).slice(0, 5).map((s) => `• ${s.label}: ${s.value}`).join("\n");
    const pageUrl = typeof window !== "undefined" ? window.location.href : "";
    const text = [
      `کالای صنعتی: ${product.name_fa}`,
      `کد کاتالوگ: ${product.sku}`,
      `واحد: ${product.unit}`,
      specs ? `مشخصات فنی کلیدی:\n${specs}` : "",
      `مشاهده جزئیات و استعلام در فروشگاه مهراصل:\n${pageUrl}`,
    ].filter(Boolean).join("\n\n");
    if (typeof navigator !== "undefined" && navigator.share) {
      try {
        await navigator.share({ title: product.name_fa, text, url: pageUrl });
        setShareFeedback("برگه فنی به اشتراک گذاشته شد.");
        setTimeout(() => setShareFeedback(null), 3000);
        return;
      } catch {
        // Fall back to clipboard if user cancels or share fails
      }
    }
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      try {
        await navigator.clipboard.writeText(text);
        setShareFeedback("مشخصات فنی و لینک کالا کپی شد.");
        setTimeout(() => setShareFeedback(null), 3000);
      } catch {
        setShareFeedback("کپی مشخصات انجام نشد.");
      }
    }
  };
  return <>
    <aside className="product-buy-panel">{identity}
      {hasVariants && !selectedVariant && <p id="variant-guidance" className="variant-guidance" role="status" aria-live="polite"><b>{missingAttributes.length ? "انتخاب مشخصات الزامی است" : "ترکیب در دسترس نیست"}</b><span>{ctaReason}</span></p>}
      {selectedVariant && <div className="variant-selection-summary" role="status" aria-live="polite"><b>پیکربندی انتخاب‌شده</b><span>{selectedSummary}</span>{selectedVariant.sku && <small dir="ltr">SKU: {selectedVariant.sku}</small>}</div>}
      <div className={`product-stock-row ${maxQuantity > 0 ? "available" : "unavailable"}`} role="status" aria-live="polite"><i aria-hidden="true" /> <strong>{maxQuantity > 0 ? "موجود" : "ناموجود"}</strong>{maxQuantity > 0 && <span>موجودی: {faNumber(maxQuantity)} {product.unit}</span>}</div>
      <ProductPurchasePanel product={domainProduct} onVariantChange={setSelectedVariant} onSelectionChange={onSelection} />
      <div className="product-cart-actions"><label htmlFor="product-quantity">تعداد</label><div className="quantity-control" aria-label="کنترل تعداد"><button type="button" onClick={() => changeQuantity(quantity - 1)} disabled={quantity <= 1 || adding || maxQuantity < 1} aria-label="کاهش تعداد">−</button><input id="product-quantity" value={formatNumber(quantity)} onChange={(event) => changeQuantity(parseFaInteger(event.target.value))} inputMode="numeric" min={maxQuantity > 0 ? 1 : undefined} max={maxQuantity > 0 ? maxQuantity : undefined} aria-describedby="quantity-help" disabled={adding || maxQuantity < 1} /><button type="button" onClick={() => changeQuantity(quantity + 1)} disabled={quantity >= maxQuantity || adding || maxQuantity < 1} aria-label="افزایش تعداد">+</button></div><small id="quantity-help" className="quantity-help">{maxQuantity > 0 ? `حداکثر ${faNumber(maxQuantity)} ${product.unit}` : ctaReason}</small><button className={`add-cart-button ${feedback?.type === "success" ? "is-success" : ""}`} type="button" onClick={addToCart} disabled={quantity < 1 || maxQuantity < 1 || adding} aria-describedby={hasVariants && !selectedVariant ? "variant-guidance" : "quantity-help"}>{ctaLabel}</button>{feedback && <p className={`cart-feedback ${feedback.type === "error" ? "is-error" : "is-success"}`} role={feedback.type === "error" ? "alert" : "status"} aria-live="polite">{feedback.text}</p>}</div>
      <div className="product-b2b-share"><button type="button" className="product-share-spec-btn" onClick={() => void shareSpecSheet()}><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg> اشتراک‌گذاری برگه فنی و استعلام تدارکات</button>{shareFeedback && <p className="share-feedback" role="status" aria-live="polite">{shareFeedback}</p>}</div>
      {product.service_advantages.length > 0 && <div className="product-services" aria-label="خدمات خرید">{product.service_advantages.map((advantage, index) => <article key={`adv-${advantage.id ?? index}`}><i aria-hidden="true">{advantage.icon || "✓"}</i><div><b>{advantage.title_fa}</b>{advantage.description_fa && <small>{advantage.description_fa}</small>}</div></article>)}</div>}
    </aside>
    <ProductGallery product={domainProduct} />
  </>;
}
