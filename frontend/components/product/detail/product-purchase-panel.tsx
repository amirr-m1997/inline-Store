"use client";
import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FiFileText, FiPhoneCall } from "react-icons/fi";
import type { ProductDetail, ProductVariant, VariantSelection } from "../../../lib/product/types";
import { formatNumber } from "../../../lib/product/formatters";
import { VariantSelector } from "./variant-selector";

export function ProductPurchasePanel({ product, onVariantChange, onSelectionChange }: { product: ProductDetail; onVariantChange?: (variant?: ProductVariant) => void; onSelectionChange?: (selection: VariantSelection) => void }) {
  const { locale = "fa" } = useParams<{ locale: string }>();
  const [variant, setVariant] = useState<ProductVariant | undefined>();
  const select = (selection: VariantSelection) => { setVariant(selection.resolvedVariant); onVariantChange?.(selection.resolvedVariant); onSelectionChange?.(selection); };
  const pricing = variant?.pricing || product.pricing;
  const discount = Number(pricing?.discountPercentage ?? 0) > 0 ? pricing?.discountPercentage : undefined;
  return (
    <>
      <VariantSelector product={product} onChange={select} />
      <div className="product-price-panel">
        {discount && <span className="product-detail-discount">٪{formatNumber(Number(discount))} تخفیف</span>}
        {pricing?.finalAmount ? (
          <>
            {discount && pricing.originalAmount && <del>{formatNumber(Number(pricing.originalAmount))} ریال</del>}
            <strong>{formatNumber(Number(pricing.finalAmount))} <small>ریال</small></strong>
          </>
        ) : (
          <div className="product-b2b-quote-card" aria-label="خرید پروژه‌ای و استعلام قیمت">
            <div className="b2b-quote-header">
              <span className="b2b-quote-dot" aria-hidden="true" />
              <b>خرید پروژه‌ای و سازمانی</b>
            </div>
            <p className="b2b-quote-note">
              قیمت این کالا متناسب با حجم پروژه، پیکربندی مهندسی و مشخصات فنی ارائه می‌گردد.
            </p>
            <div className="b2b-quote-actions">
              <Link
                className="b2b-quote-action-btn primary"
                href={`/${locale}/rfq?product=${encodeURIComponent(product.slug)}`}
              >
                <FiFileText size={16} aria-hidden="true" />
                <span>استعلام قیمت سریع</span>
              </Link>
              <a
                className="b2b-quote-action-btn secondary"
                href="tel:02188300801"
                aria-label="تماس با مهندس فروش"
              >
                <FiPhoneCall size={15} aria-hidden="true" />
                <span>گفت‌وگو با مهندس فروش</span>
              </a>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
