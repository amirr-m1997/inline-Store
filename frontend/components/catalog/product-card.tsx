import Image from "next/image";
import Link from "next/link";

export type CatalogProduct = {
  id: number;
  name: string;
  slug: string;
  code: string;
  unit: string;
  available_quantity: number | null;
  category: { name_fa: string } | null;
  images: { image: string; alt_text: string; alt_fa?: string; is_primary?: boolean }[];
  price: { original_amount: string; final_amount: string; discount_percentage: string } | null;
};

const money = (value: string) => Number(value).toLocaleString("fa-IR", { maximumFractionDigits: 0 });

export function ProductCard({ product, priority = false }: { product: CatalogProduct; priority?: boolean }) {
  const image = product.images.find((item) => item.is_primary) ?? product.images[0];
  const discount = Number(product.price?.discount_percentage ?? 0);
  const inStock = (product.available_quantity ?? 0) > 0;
  return <article className="industrial-product-card">
    <Link className="industrial-card-image" href={`/fa/product/${product.slug}`} aria-label={`مشاهده ${product.name}`}>
      {image ? <Image src={image.image} alt={image.alt_fa || image.alt_text || product.name} fill priority={priority} sizes="(max-width: 520px) 92vw, (max-width: 850px) 46vw, (max-width: 1200px) 30vw, 280px" /> : <span className="industrial-image-placeholder"><i aria-hidden="true">◇</i><b>تصویر محصول ثبت نشده است</b><small>کد کالا در جزئیات موجود است</small></span>}
      {discount > 0 && <strong className="industrial-discount-badge">٪{discount.toLocaleString("fa-IR")} تخفیف</strong>}
    </Link>
    <div className="industrial-card-content">
      <span className="industrial-card-category">{product.category?.name_fa || "بدون دسته‌بندی"}</span>
      <Link className="industrial-card-title" href={`/fa/product/${product.slug}`}>{product.name}</Link>
      <p className="industrial-card-code">کد کالا: <bdi dir="ltr">{product.code}</bdi></p>
      <div className="industrial-card-status"><span className={inStock ? "available" : "unavailable"}><i />{product.available_quantity === null ? "موجودی نامشخص" : inStock ? "موجود" : "ناموجود"}</span><small>واحد: {product.unit}</small></div>
      <div className="industrial-card-price">
        {product.price ? <>{discount > 0 && <del>{money(product.price.original_amount)} ریال</del>}<strong>{money(product.price.final_amount)} <small>ریال</small></strong></> : <span>قیمت ثبت نشده است</span>}
      </div>
    </div>
    <footer className="industrial-card-actions"><Link href={`/fa/product/${product.slug}`}>مشاهده جزئیات <span aria-hidden="true">←</span></Link></footer>
  </article>;
}

export function ProductCardSkeleton() {
  return <div className="industrial-product-card animate-pulse bg-slate-50/50 p-4 rounded-xl border border-slate-200/60 shadow-sm">
    <div className="h-48 w-full rounded-lg bg-slate-200" />
    <div className="mt-4 h-3 w-1/4 rounded bg-slate-200" />
    <div className="mt-2 h-5 w-4/5 rounded bg-slate-200" />
    <div className="mt-2 h-3 w-1/3 rounded bg-slate-200" />
    <div className="mt-4 flex items-center justify-between">
      <div className="h-4 w-1/3 rounded bg-slate-200" />
      <div className="h-4 w-1/4 rounded bg-slate-200" />
    </div>
    <div className="mt-4 h-10 w-full rounded-lg bg-slate-200" />
  </div>;
}
