import Image from "next/image";
import Link from "next/link";
import { Button } from "../../ui/button";
import type { ProductSummary } from "../../../lib/product/types";
import { formatProductMoney, hasDiscount, isAvailable } from "../../../lib/product/formatters";

export function ProductCard({ product, priority = false, locale = "fa" }: { product: ProductSummary; priority?: boolean; locale?: string }) {
  const image = product.media.find((item) => item.isPrimary) ?? product.media[0];
  const discount = hasDiscount(product.pricing);
  const available = isAvailable(product.availability);
  const productHref = `/${locale}/product/${product.slug}`;
  return <article className="industrial-product-card"><Link className="industrial-card-image" href={productHref} aria-label={`مشاهده ${product.name}`}>{image ? <Image src={image.url} alt={image.alt || product.name} fill priority={priority} sizes="(max-width: 520px) 92vw, (max-width: 850px) 46vw, (max-width: 1200px) 30vw, 280px" /> : <span className="industrial-image-placeholder"><i aria-hidden="true">◇</i><b>تصویر محصول ثبت نشده است</b><small>کد کالا در جزئیات موجود است</small></span>}{discount && <strong className="industrial-discount-badge">٪{Number(product.pricing?.discountPercentage).toLocaleString("fa-IR")} تخفیف</strong>}</Link><div className="industrial-card-content"><span className="industrial-card-category">{product.category?.name || "بدون دسته‌بندی"}</span>{product.brand && <small>{product.brand}</small>}<Link className="industrial-card-title" href={productHref}>{product.name}</Link><p className="industrial-card-code">کد کالا: <bdi dir="ltr">{product.sku || product.code}</bdi></p><div className="industrial-card-status"><span className={available ? "available" : "unavailable"}><i />{product.availability.quantity === null ? "موجودی نامشخص" : available ? "موجود" : "ناموجود"}</span><small>واحد: {product.unit}</small>{product.documents?.length ? <small>مدارک فنی موجود است</small> : null}</div><div className="industrial-card-price">{product.pricing?.finalAmount ? <>{discount && <del>{formatProductMoney(product.pricing.originalAmount)} ریال</del>}<strong>{formatProductMoney(product.pricing.finalAmount)} <small>ریال</small></strong></> : <span>{product.purchaseMode === "quote" ? "نیازمند استعلام قیمت" : "قیمت ثبت نشده است"}</span>}</div></div><footer className="industrial-card-actions"><Button href={productHref} variant="ghost" size="sm">{product.purchaseMode === "quote" ? "استعلام قیمت" : "مشاهده جزئیات"} <span aria-hidden="true">←</span></Button></footer></article>;
}
