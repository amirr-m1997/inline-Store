import Image from "next/image";
import Link from "next/link";
import { Button } from "../../ui/button";
import type { ProductSummary } from "../../../lib/product/types";
import { formatProductMoney, formatNumber, hasDiscount, isAvailable } from "../../../lib/product/formatters";

export function ProductCard({ product, priority = false, locale = "fa" }: { product: ProductSummary; priority?: boolean; locale?: string }) {
  const english = locale === "en";
  const image = product.media.find((item) => item.isPrimary) ?? product.media[0];
  const discount = hasDiscount(product.pricing);
  const available = isAvailable(product.availability);
  const productHref = `/${locale}/product/${product.slug}`;

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
        {discount && (
          <strong className="industrial-discount-badge">
            {english
              ? `${formatNumber(Number(product.pricing?.discountPercentage))}% off`
              : `٪${formatNumber(Number(product.pricing?.discountPercentage))} تخفیف`}
          </strong>
        )}
      </Link>

      <div className="industrial-card-content">
        <div className="industrial-card-meta">
          <span className="industrial-card-category">
            {product.category?.name || (english ? "Uncategorized" : "بدون دسته‌بندی")}
          </span>
          {product.brand && <small className="industrial-card-brand">{product.brand}</small>}
        </div>

        <Link className="industrial-card-title" href={productHref}>
          {product.name}
        </Link>
        {product.shortDescription && (
          <p className="industrial-card-excerpt">{product.shortDescription}</p>
        )}

        <p className="industrial-card-code">
          <span>{english ? "Product code" : "کد کالا"}:</span> <bdi dir="ltr">{product.sku || product.code}</bdi>
        </p>

        <div className="industrial-card-status">
          <span className={available ? "available" : "unavailable"}>
            <i aria-hidden="true" />
            {product.availability.quantity === null
              ? (english ? "Unknown stock" : "موجودی نامشخص")
              : available
              ? (english ? "In stock" : "موجود")
              : (english ? "Out of stock" : "ناموجود")}
          </span>
          <small>{english ? "Unit" : "واحد"}: {product.unit}</small>
          {product.documents?.length ? (
            <small className="industrial-card-docs-tag">{english ? "Technical docs" : "مدارک فنی"}</small>
          ) : null}
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
            <span className="industrial-card-price-quote">
              {product.purchaseMode === "quote"
                ? (english ? "Price on request" : "نیازمند استعلام قیمت")
                : (english ? "Price not listed" : "قیمت ثبت نشده است")}
            </span>
          )}
        </div>
      </div>

      <footer className="industrial-card-actions">
        <Button href={productHref} variant="ghost" size="sm" className="industrial-card-cta">
          <span>{product.purchaseMode === "quote" ? (english ? "Request a quote" : "استعلام قیمت") : (english ? "View details" : "مشاهده جزئیات")}</span>
          <span aria-hidden="true" className="rtl:rotate-180 inline-block">←</span>
        </Button>
      </footer>
    </article>
  );
}
