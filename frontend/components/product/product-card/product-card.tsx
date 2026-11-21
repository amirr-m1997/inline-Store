"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { FiCheck, FiCopy, FiFileText } from "react-icons/fi";
import { Button } from "../../ui/button";
import type { ProductSummary } from "../../../lib/product/types";
import { formatProductMoney, formatNumber, hasDiscount, isAvailable } from "../../../lib/product/formatters";

export function ProductCard({ product, priority = false, locale = "fa" }: { product: ProductSummary; priority?: boolean; locale?: string }) {
  const [copiedSku, setCopiedSku] = useState(false);
  const english = locale === "en";
  const image = product.media.find((item) => item.isPrimary) ?? product.media[0];
  const discount = hasDiscount(product.pricing);
  const available = isAvailable(product.availability);
  const quoteInPrice = !product.pricing?.finalAmount;
  const productHref = `/${locale}/product/${product.slug}`;
  const productCode = product.sku || product.code;
  const hasDocuments = Boolean(product.documents && product.documents.length > 0);

  const handleCopyCode = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!productCode) return;

    try {
      if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(productCode);
      } else {
        const input = document.createElement("input");
        input.value = productCode;
        input.style.position = "fixed";
        input.style.opacity = "0";
        document.body.appendChild(input);
        input.select();
        document.execCommand("copy");
        document.body.removeChild(input);
      }
      setCopiedSku(true);
      setTimeout(() => setCopiedSku(false), 2000);
    } catch {
      /* ignore copy errors */
    }
  };

  return (
    <article className="industrial-product-card">
      <Link
        className="industrial-card-image"
        href={productHref}
        aria-label={`${english ? "View" : "مشاهده"} ${product.name}`}
      >
        {image ? (
          <Image
            src={image.url}
            alt={image.alt || product.name}
            fill
            priority={priority}
            sizes="(max-width: 640px) 90vw, (max-width: 1024px) 45vw, 280px"
          />
        ) : (
          <span className="industrial-image-placeholder">
            <i aria-hidden="true">◇</i>
            <b>{english ? "No product image registered" : "تصویر محصول ثبت نشده است"}</b>
            <small>{english ? "See details for product code" : "کد کالا در جزئیات موجود است"}</small>
          </span>
        )}

        <div className="industrial-card-badges-overlay">
          {discount && (
            <strong className="industrial-discount-badge">
              {english
                ? `${formatNumber(Number(product.pricing?.discountPercentage))}% OFF`
                : `٪${formatNumber(Number(product.pricing?.discountPercentage))} تخفیف`}
            </strong>
          )}
          {hasDocuments && (
            <span className="industrial-pdf-badge" title={english ? "Technical datasheet PDF available" : "دیتاشیت فنی رسمی موجود است"}>
              <FiFileText aria-hidden="true" />
              <span>PDF</span>
            </span>
          )}
        </div>
      </Link>

      <div className="industrial-card-content">
        <div className="industrial-card-meta">
          <span className="industrial-card-category">
            {product.category?.name || (english ? "Equipment" : "تجهیزات صنعتی")}
          </span>
          {product.brand && <small className="industrial-card-brand">{product.brand}</small>}
        </div>

        <Link className="industrial-card-title line-clamp-2" href={productHref} title={product.name}>
          {product.name}
        </Link>
        {product.shortDescription && (
          <p className="industrial-card-excerpt line-clamp-2">{product.shortDescription}</p>
        )}

        <div className="industrial-card-code-row">
          <p className="industrial-card-code">
            <span>{english ? "SKU" : "کد کالا"}:</span> <bdi dir="ltr">{productCode}</bdi>
          </p>
          <button
            type="button"
            className="industrial-card-code-copy-btn"
            onClick={handleCopyCode}
            aria-label={english ? "Copy SKU" : "کپی کد کالا"}
            title={copiedSku ? (english ? "Copied!" : "کپی شد!") : (english ? "Copy SKU" : "کپی کد کالا")}
          >
            {copiedSku ? (
              <>
                <FiCheck className="text-emerald-500" aria-hidden="true" />
                <span className="copy-feedback-text">{english ? "Copied" : "کپی شد"}</span>
              </>
            ) : (
              <FiCopy aria-hidden="true" />
            )}
          </button>
        </div>

        <div className="industrial-card-status">
          <span className={available ? "available" : "unavailable"}>
            <i aria-hidden="true" className="stock-dot" />
            {product.availability.quantity === null
              ? (english ? "Unknown stock" : "موجودی نامشخص")
              : available
              ? (english ? "In stock" : "موجود")
              : (english ? "Out of stock" : "ناموجود")}
          </span>
          <small className="industrial-card-unit">{english ? "Unit" : "واحد"}: {product.unit}</small>
        </div>

        <div className="industrial-card-price">
          {product.pricing?.finalAmount ? (
            <>
              {discount && (
                <del className="industrial-card-old-price">
                  {formatProductMoney(product.pricing.originalAmount, locale)} {english ? "IRR" : "ریال"}
                </del>
              )}
              <strong className="industrial-card-final-price">
                {formatProductMoney(product.pricing.finalAmount, locale)} <small>{english ? "IRR" : "ریال"}</small>
              </strong>
            </>
          ) : (
            <Link
              className="industrial-card-quote-btn"
              href={`/${locale}/rfq?product=${encodeURIComponent(product.slug)}`}
            >
              {english ? "Request a quote" : "استعلام قیمت سریع"}
            </Link>
          )}
        </div>
      </div>

      <footer className="industrial-card-actions">
        <Button href={productHref} variant="ghost" size="sm" className="industrial-card-cta">
          <span>{!quoteInPrice && product.purchaseMode === "quote" ? (english ? "Request a quote" : "استعلام قیمت") : (english ? "View details" : "مشاهده جزئیات")}</span>
          <span aria-hidden="true">←</span>
        </Button>
      </footer>
    </article>
  );
}
