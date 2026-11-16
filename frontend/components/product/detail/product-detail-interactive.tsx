"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import { FaWhatsapp, FaTelegramPlane } from "react-icons/fa";
import { FiCopy, FiCheck, FiShare2 } from "react-icons/fi";
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
  const getShareText = () => {
    const specs = (product.technical_specifications || []).slice(0, 5).map((s) => `• ${s.label}: ${s.value}`).join("\n");
    const pageUrl = typeof window !== "undefined" ? window.location.href : "";
    return [
      `کالای صنعتی: ${product.name_fa}`,
      `کد کاتالوگ: ${product.sku}`,
      `واحد: ${product.unit}`,
      specs ? `مشخصات فنی کلیدی:\n${specs}` : "",
      `مشاهده جزئیات و استعلام در فروشگاه مهراصل:\n${pageUrl}`,
    ].filter(Boolean).join("\n\n");
  };

  const copySpecSheet = async () => {
    const text = getShareText();
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      try {
        await navigator.clipboard.writeText(text);
        setShareFeedback("مشخصات فنی و لینک کالا در حافظه (Clipboard) کپی شد. اکنون می‌توانید آن را در پیام‌رسان یا ایمیل الصاق (Paste) نمایید.");
        setTimeout(() => setShareFeedback(null), 5000);
        return;
      } catch {
        // fallback
      }
    }
    try {
      const input = document.createElement("textarea");
      input.value = text;
      input.style.position = "fixed";
      input.style.opacity = "0";
      document.body.appendChild(input);
      input.focus();
      input.select();
      const success = document.execCommand("copy");
      document.body.removeChild(input);
      if (success) {
        setShareFeedback("مشخصات فنی و لینک کالا در حافظه (Clipboard) کپی شد. اکنون می‌توانید آن را در پیام‌رسان یا ایمیل الصاق (Paste) نمایید.");
        setTimeout(() => setShareFeedback(null), 5000);
        return;
      }
    } catch {
      // ignore
    }
    setShareFeedback("کپی انجام نشد. لطفاً لینک را دستی کپی نمایید.");
  };

  const shareSpecSheet = async () => {
    const text = getShareText();
    const pageUrl = typeof window !== "undefined" ? window.location.href : "";
    if (typeof navigator !== "undefined" && navigator.share) {
      try {
        await navigator.share({ title: product.name_fa, text, url: pageUrl });
        setShareFeedback("منوی اشتراک‌گذاری سیستم باز شد.");
        setTimeout(() => setShareFeedback(null), 4000);
        return;
      } catch {
        // Fall back to copy
      }
    }
    await copySpecSheet();
  };

  const openSocialShare = (platform: "whatsapp" | "telegram" | "eitaa" | "bale") => {
    const text = getShareText();
    const encodedText = encodeURIComponent(text);
    const pageUrl = typeof window !== "undefined" ? encodeURIComponent(window.location.href) : "";
    let url = "";

    switch (platform) {
      case "whatsapp":
        url = `https://api.whatsapp.com/send?text=${encodedText}`;
        break;
      case "telegram":
        url = `https://t.me/share/url?url=${pageUrl}&text=${encodedText}`;
        break;
      case "eitaa":
        url = `https://eitaa.com/share/url?url=${pageUrl}&text=${encodedText}`;
        break;
      case "bale":
        url = `https://ble.ir/share/compile?url=${pageUrl}&text=${encodedText}`;
        break;
    }

    if (url) {
      window.open(url, "_blank", "noopener,noreferrer");
    }
  };
  return <>
    <aside className="product-buy-panel">{identity}
      {hasVariants && !selectedVariant && <p id="variant-guidance" className="variant-guidance" role="status" aria-live="polite"><b>{missingAttributes.length ? "انتخاب مشخصات الزامی است" : "ترکیب در دسترس نیست"}</b><span>{ctaReason}</span></p>}
      {selectedVariant && <div className="variant-selection-summary" role="status" aria-live="polite"><b>پیکربندی انتخاب‌شده</b><span>{selectedSummary}</span>{selectedVariant.sku && <small dir="ltr">SKU: {selectedVariant.sku}</small>}</div>}
      <div className={`product-stock-row ${maxQuantity > 0 ? "available" : "unavailable"}`} role="status" aria-live="polite"><i aria-hidden="true" /> <strong>{maxQuantity > 0 ? "موجود" : "ناموجود"}</strong>{maxQuantity > 0 && <span>موجودی: {faNumber(maxQuantity)} {product.unit}</span>}</div>
      <ProductPurchasePanel product={domainProduct} onVariantChange={setSelectedVariant} onSelectionChange={onSelection} />
      <div className="product-cart-actions"><label htmlFor="product-quantity">تعداد</label><div className="quantity-control" aria-label="کنترل تعداد"><button type="button" onClick={() => changeQuantity(quantity - 1)} disabled={quantity <= 1 || adding || maxQuantity < 1} aria-label="کاهش تعداد">−</button><input id="product-quantity" value={formatNumber(quantity)} onChange={(event) => changeQuantity(parseFaInteger(event.target.value))} inputMode="numeric" min={maxQuantity > 0 ? 1 : undefined} max={maxQuantity > 0 ? maxQuantity : undefined} aria-describedby="quantity-help" disabled={adding || maxQuantity < 1} /><button type="button" onClick={() => changeQuantity(quantity + 1)} disabled={quantity >= maxQuantity || adding || maxQuantity < 1} aria-label="افزایش تعداد">+</button></div><small id="quantity-help" className="quantity-help">{maxQuantity > 0 ? `حداکثر ${faNumber(maxQuantity)} ${product.unit}` : ctaReason}</small><button className={`add-cart-button ${feedback?.type === "success" ? "is-success" : ""}`} type="button" onClick={addToCart} disabled={quantity < 1 || maxQuantity < 1 || adding} aria-describedby={hasVariants && !selectedVariant ? "variant-guidance" : "quantity-help"}>{ctaLabel}</button>{feedback && <p className={`cart-feedback ${feedback.type === "error" ? "is-error" : "is-success"}`} role={feedback.type === "error" ? "alert" : "status"} aria-live="polite">{feedback.text}</p>}</div>
      <div className="product-b2b-share">
        <div className="product-share-actions-group">
          <button type="button" className="product-share-spec-btn" onClick={() => void copySpecSheet()} title="کپی متن کامل مشخصات فنی و لینک در کلیپ‌بورد">
            <FiCopy size={14} aria-hidden="true" />
            <span>کپی برگه فنی و استعلام</span>
          </button>
          <div className="product-social-share-row" aria-label="اشتراک در شبکه‌های اجتماعی">
            <span className="product-social-share-label">ارسال سریع:</span>
            <button
              type="button"
              className="social-share-icon-btn whatsapp"
              onClick={() => openSocialShare("whatsapp")}
              title="ارسال در واتساپ"
              aria-label="ارسال برگه فنی در واتساپ"
            >
              <FaWhatsapp size={15} aria-hidden="true" />
              <span>واتساپ</span>
            </button>
            <button
              type="button"
              className="social-share-icon-btn telegram"
              onClick={() => openSocialShare("telegram")}
              title="ارسال در تلگرام"
              aria-label="ارسال برگه فنی در تلگرام"
            >
              <FaTelegramPlane size={15} aria-hidden="true" />
              <span>تلگرام</span>
            </button>
            <button
              type="button"
              className="social-share-icon-btn eitaa"
              onClick={() => openSocialShare("eitaa")}
              title="ارسال در ایتا"
              aria-label="ارسال برگه فنی در ایتا"
            >
              <span className="messenger-text-badge" aria-hidden="true">ایتا</span>
            </button>
            <button
              type="button"
              className="social-share-icon-btn bale"
              onClick={() => openSocialShare("bale")}
              title="ارسال در بله"
              aria-label="ارسال برگه فنی در بله"
            >
              <span className="messenger-text-badge" aria-hidden="true">بله</span>
            </button>
            <button
              type="button"
              className="social-share-icon-btn native-share"
              onClick={() => void shareSpecSheet()}
              title="سایر روش‌های اشتراک‌گذاری سیستم"
              aria-label="اشتراک‌گذاری با سایر برنامه‌ها"
            >
              <FiShare2 size={13} aria-hidden="true" />
            </button>
          </div>
        </div>
        {shareFeedback && <p className="share-feedback" role="status" aria-live="polite">{shareFeedback}</p>}
      </div>
      {product.service_advantages.length > 0 && <div className="product-services" aria-label="خدمات خرید">{product.service_advantages.map((advantage, index) => <article key={`adv-${advantage.id ?? index}`}><i aria-hidden="true">{advantage.icon || "✓"}</i><div><b>{advantage.title_fa}</b>{advantage.description_fa && <small>{advantage.description_fa}</small>}</div></article>)}</div>}
    </aside>
    <ProductGallery product={domainProduct} />
  </>;
}
