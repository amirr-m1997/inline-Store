"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { getCategoryUrl } from "../../../../lib/category-url";

type ProductImage = { id: number; url: string; alt_fa: string; alt_en: string; alt_text: string; is_primary: boolean };
type ProductSummary = { id: number; slug: string; code: string; name_fa: string; unit: string; primary_image: string | null };
type ServiceAdvantage = { id: number; title_fa: string; title_en: string; description_fa: string; description_en: string; icon: string };
type ProductDetail = {
  id: number; slug: string; name_fa: string; name_en: string; sku: string; unit: string; description: string;
  images: ProductImage[]; category_tree: { id: number; name_fa: string; slug: string }[];
  inventory: { available: number | null; reserved: number | null; net: number | null; allowed_for_cart: number; last_receipt_date: string | null; last_issue_date: string | null };
  pricing: { price: string | null; currency: string | null; discount_percentage: string | null; final_price: string | null; last_purchase_irr: string | null; receipt_usd_rate: string | null; last_purchase_usd: string | null; today_irr_equivalent: string | null };
  technical_specifications: { label: string; value: unknown }[];
  related_products: ProductSummary[];
  service_advantages: ServiceAdvantage[];
};

const faDigits = (value: string) => value.replace(/\d/g, (digit) => "۰۱۲۳۴۵۶۷۸۹"[Number(digit)]);
const money = (value: string | null) => {
  if (!value) return "ثبت نشده";
  const [integer, decimals] = value.split(".");
  const grouped = integer.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  const fraction = decimals?.replace(/0+$/, "");
  return faDigits(fraction ? `${grouped}.${fraction}` : grouped);
};
const faNumber = (value: number | null) => value === null ? "ثبت نشده" : value.toLocaleString("fa-IR");
const parseFaInteger = (value: string) => Number(value.replace(/[۰-۹]/g, (digit) => String("۰۱۲۳۴۵۶۷۸۹".indexOf(digit))).replace(/\D/g, ""));

export default function ProductPage({ params }: { params: Promise<{ locale: string; slug: string }> }) {
  const [route, setRoute] = useState<{ locale: string; slug: string } | null>(null);
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [activeImage, setActiveImage] = useState(0);
  const [quantity, setQuantity] = useState(1);
  const [activeTab, setActiveTab] = useState<"specs" | "description">("specs");
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => { params.then(setRoute); }, [params]);
  useEffect(() => {
    if (!route) return;
    const controller = new AbortController();
    setLoading(true); setError("");
    fetch(`/api/v1/catalog/products/${encodeURIComponent(route.slug)}/`, { signal: controller.signal })
      .then(async (response) => { if (!response.ok) throw new Error(response.status === 404 ? "محصول موردنظر پیدا نشد." : "دریافت اطلاعات محصول ناموفق بود."); return response.json() as Promise<ProductDetail>; })
      .then((data) => {
        setProduct(data);
        const primary = data.images.findIndex((image) => image.is_primary);
        setActiveImage(primary >= 0 ? primary : 0);
        setQuantity(data.inventory.allowed_for_cart > 0 ? 1 : 0);
      })
      .catch((reason: Error) => { if (reason.name !== "AbortError") setError(reason.message); })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [route]);

  const images = useMemo(() => product?.images ?? [], [product]);
  const maxQuantity = product?.inventory.allowed_for_cart ?? 0;
  const locale = route?.locale ?? "fa";
  const changeQuantity = (next: number) => setQuantity(maxQuantity > 0 ? Math.min(maxQuantity, Math.max(1, Number.isFinite(next) ? next : 1)) : 0);
  const moveImage = (direction: number) => { if (images.length > 1) setActiveImage((current) => (current + direction + images.length) % images.length); };
  const addToCart = async () => {
    if (!product || quantity < 1 || adding) return;
    setAdding(true); setMessage("");
    try {
      const guestToken = window.localStorage.getItem("guestCartToken");
      const response = await fetch("/api/v1/cart/items/", { method: "POST", headers: { "Content-Type": "application/json", ...(guestToken ? { "X-Guest-Token": guestToken } : {}) }, body: JSON.stringify({ product_id: product.id, quantity }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "افزودن محصول به سبد ناموفق بود.");
      if (payload.guest_token) window.localStorage.setItem("guestCartToken", payload.guest_token);
      window.dispatchEvent(new Event("cart-updated"));
      setMessage("محصول با موفقیت به سبد خرید افزوده شد.");
    } catch (reason) { setMessage(reason instanceof Error ? reason.message : "خطایی رخ داد."); }
    finally { setAdding(false); }
  };

  if (loading) return <main className="product-detail-page site-container"><div className="product-state">در حال دریافت اطلاعات محصول…</div></main>;
  if (error || !product) return <main className="product-detail-page site-container"><div className="product-state product-error">{error || "محصول پیدا نشد."}</div></main>;
  const currentImage = images[activeImage];
  const discount = product.pricing.discount_percentage && product.pricing.discount_percentage !== "0.00" ? product.pricing.discount_percentage : null;
  const finalCategory = product.category_tree.at(-1);

  return <main className="product-detail-page site-container" dir={locale === "fa" ? "rtl" : "ltr"}>
    <nav className="product-breadcrumb" aria-label="مسیر صفحه">
      <Link href={`/${locale}`}>خانه</Link>
      {product.category_tree.map((category) => <span className="breadcrumb-part" key={category.id}><span>/</span><Link href={getCategoryUrl(category, locale)}>{category.name_fa}</Link></span>)}
      <span>/</span><b>{product.name_fa}</b>
    </nav>

    <section className="product-purchase-layout">
      <aside className="product-buy-panel">
        <span className="product-eyebrow">{finalCategory?.name_fa || "محصول"}</span>
        <h1>{product.name_fa}</h1>
        {product.name_en && <p className="product-en-name" dir="ltr">{product.name_en}</p>}
        <div className="product-code-row"><span>کد کالا:</span><b dir="ltr">{product.sku}</b></div>
        <div className={`product-stock-row ${maxQuantity > 0 ? "available" : "unavailable"}`}><i /> <strong>{maxQuantity > 0 ? "موجود" : "ناموجود"}</strong>{maxQuantity > 0 && <span>موجودی: {faNumber(maxQuantity)} {product.unit}</span>}</div>

        <div className="product-price-panel">
          {discount && <span className="product-detail-discount">٪{money(discount)} تخفیف</span>}
          {product.pricing.final_price ? <>{discount && <del>{money(product.pricing.price)} ریال</del>}<strong>{money(product.pricing.final_price)} <small>ریال</small></strong></> : <p>قیمت برای این محصول ثبت نشده است.</p>}
        </div>

        <div className="product-cart-actions">
          <label htmlFor="product-quantity">تعداد</label>
          <div className="quantity-control"><button type="button" onClick={() => changeQuantity(quantity - 1)} disabled={quantity <= 1 || adding || maxQuantity < 1} aria-label="کاهش تعداد">−</button><input id="product-quantity" value={quantity.toLocaleString("fa-IR")} onChange={(event) => changeQuantity(parseFaInteger(event.target.value))} inputMode="numeric" disabled={adding || maxQuantity < 1} /><button type="button" onClick={() => changeQuantity(quantity + 1)} disabled={quantity >= maxQuantity || adding || maxQuantity < 1} aria-label="افزایش تعداد">+</button></div>
          <button className="add-cart-button" type="button" onClick={addToCart} disabled={quantity < 1 || maxQuantity < 1 || adding}>{adding ? "در حال افزودن…" : "افزودن به سبد خرید"}</button>
          {message && <p className="cart-feedback" role="status">{message}</p>}
        </div>

        {product.service_advantages.length > 0 && <div className="product-services" aria-label="خدمات خرید">{product.service_advantages.map((advantage) => <article key={advantage.id}><i aria-hidden="true">{advantage.icon || "✓"}</i><div><b>{advantage.title_fa}</b>{advantage.description_fa && <small>{advantage.description_fa}</small>}</div></article>)}</div>}
      </aside>

      <div className="product-gallery-workspace">
        <div className="gallery-stage">
          {currentImage ? <Image src={currentImage.url} alt={currentImage.alt_fa || currentImage.alt_text || product.name_fa} fill priority sizes="(max-width: 720px) 92vw, (max-width: 1100px) 52vw, 560px" /> : <div className="gallery-placeholder"><span>◇</span><b>تصویری برای این محصول ثبت نشده است</b><small>کد کالا: {product.sku}</small></div>}
          {images.length > 1 && <><button className="gallery-nav gallery-next" type="button" onClick={() => moveImage(1)} aria-label="تصویر بعدی">‹</button><button className="gallery-nav gallery-prev" type="button" onClick={() => moveImage(-1)} aria-label="تصویر قبلی">›</button></>}
        </div>
        {images.length > 1 && <div className="gallery-thumbnails" aria-label="تصاویر محصول">{images.map((image, index) => <button type="button" className={index === activeImage ? "active" : ""} key={image.id} onClick={() => setActiveImage(index)} aria-label={`نمایش تصویر ${index + 1}`} aria-current={index === activeImage ? "true" : undefined}><Image src={image.url} alt={image.alt_fa || image.alt_text || product.name_fa} fill sizes="72px" /></button>)}</div>}
      </div>
    </section>

    <section className="product-detail-tabs">
      <div className="product-tab-list" role="tablist" aria-label="اطلاعات محصول">
        <button type="button" role="tab" aria-selected={activeTab === "specs"} onClick={() => setActiveTab("specs")}>مشخصات فنی</button>
        {product.description && <button type="button" role="tab" aria-selected={activeTab === "description"} onClick={() => setActiveTab("description")}>معرفی محصول</button>}
        <button className="future-tab" type="button" role="tab" aria-selected="false" disabled>نظرات <small>به‌زودی</small></button>
        <button className="future-tab" type="button" role="tab" aria-selected="false" disabled>پرسش و پاسخ <small>به‌زودی</small></button>
      </div>
      {activeTab === "specs" ? <div className="product-spec-table" role="tabpanel">{product.technical_specifications.length ? <dl>{product.technical_specifications.map((spec) => <div key={spec.label}><dt>{spec.label}</dt><dd>{String(spec.value)}</dd></div>)}</dl> : <p className="empty-section">مشخصات فنی برای این کالا ثبت نشده است.</p>}</div> : <div className="product-description-tab" role="tabpanel"><p>{product.description}</p></div>}
    </section>

    {product.related_products.length > 0 && <section className="related-section"><header><div><span>از همین گروه کالا</span><h2>محصولات مرتبط</h2></div>{finalCategory && <Link href={getCategoryUrl(finalCategory, locale)}>مشاهده دسته‌بندی ←</Link>}</header><div className="related-grid">{product.related_products.map((item) => <Link href={`/${locale}/product/${item.slug}`} key={item.id}><div>{item.primary_image ? <Image src={item.primary_image} alt={item.name_fa} fill sizes="180px" /> : <span>بدون تصویر</span>}</div><small>{item.code}</small><h3>{item.name_fa}</h3><p>واحد: {item.unit}</p></Link>)}</div></section>}
  </main>;
}
