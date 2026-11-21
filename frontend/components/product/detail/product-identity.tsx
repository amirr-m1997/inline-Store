"use client";

import { useState } from "react";
import { FiShare2, FiCheck, FiCopy, FiFileText } from "react-icons/fi";
import type { ProductDetail } from "../../../lib/product/types";
import { formatNumber } from "../../../lib/product/formatters";

export function ProductIdentity({ product }: { product: ProductDetail }) {
  const [copied, setCopied] = useState(false);
  const [skuCopied, setSkuCopied] = useState(false);

  const copyToClipboard = async (text: string): Promise<boolean> => {
    if (typeof navigator !== "undefined" && navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      try {
        await navigator.clipboard.writeText(text);
        return true;
      } catch {
        /* fallback */
      }
    }
    try {
      const input = document.createElement("input");
      input.value = text;
      input.style.position = "fixed";
      input.style.opacity = "0";
      document.body.appendChild(input);
      input.focus();
      input.select();
      const success = document.execCommand("copy");
      document.body.removeChild(input);
      return Boolean(success);
    } catch {
      return false;
    }
  };

  const handleCopySku = async () => {
    const code = product.sku || product.code;
    const success = await copyToClipboard(code);
    if (success) {
      setSkuCopied(true);
      setTimeout(() => setSkuCopied(false), 2500);
    }
  };

  const handleShare = async () => {
    const url = typeof window !== "undefined" ? window.location.href : "";
    if (typeof navigator !== "undefined" && typeof navigator.share === "function") {
      try {
        await navigator.share({ title: product.name, url });
        return;
      } catch (err) {
        if (err && typeof err === "object" && "name" in err && (err as { name: string }).name === "AbortError") return;
      }
    }

    const success = await copyToClipboard(url);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    }
  };

  const docCount = product.documents?.length ?? 0;

  return (
    <div className="product-identity-block">
      <div className="product-identity-header-row">
        <span className="product-eyebrow">{product.categories.at(-1)?.name || "محصول"}</span>
        <button
          type="button"
          onClick={handleShare}
          className="product-detail-share-btn"
          title="اشتراک‌گذاری محصول"
          aria-label="اشتراک‌گذاری محصول"
        >
          {copied ? <FiCheck size={15} /> : <FiShare2 size={15} />}
          <span>{copied ? "کپی شد" : "اشتراک‌گذاری"}</span>
        </button>
      </div>
      <h1>{product.name}</h1>
      {product.nameEn && <p className="product-en-name" dir="ltr">{product.nameEn}</p>}
      {product.brand && <p className="product-brand">{product.brand}</p>}
      <div className="product-code-row">
        <div className="product-code-meta">
          <span>کد کالا:</span>
          <b dir="ltr">{product.sku || product.code}</b>
          <button
            type="button"
            onClick={handleCopySku}
            className={`product-code-copy-btn${skuCopied ? " is-copied" : ""}`}
            title="کپی کد کالا برای پیش‌فاکتور و استعلام"
            aria-label="کپی کد کالا"
          >
            {skuCopied ? <FiCheck size={13} aria-hidden="true" /> : <FiCopy size={13} aria-hidden="true" />}
            <span>{skuCopied ? "کپی شد!" : "کپی کد"}</span>
          </button>
        </div>
        {docCount > 0 && (
          <a
            href="#product-documents-section"
            className="product-datasheet-quick-badge"
            title="مشاهده و دانلود مدارک و کاتالوگ‌های فنی"
          >
            <FiFileText size={14} aria-hidden="true" />
            <span>📄 دانلود دیتاشیت رسمی ({formatNumber(docCount)} سند)</span>
          </a>
        )}
      </div>
    </div>
  );
}
