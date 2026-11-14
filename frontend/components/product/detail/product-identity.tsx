"use client";

import { useState } from "react";
import { FiShare2, FiCheck } from "react-icons/fi";
import type { ProductDetail } from "../../../lib/product/types";

export function ProductIdentity({ product }: { product: ProductDetail }) {
  const [copied, setCopied] = useState(false);

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

    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
        await navigator.clipboard.writeText(url);
        setCopied(true);
        setTimeout(() => setCopied(false), 3000);
        return;
      }
    } catch { /* clipboard rejected */ }

    try {
      const input = document.createElement("input");
      input.value = url;
      input.style.position = "fixed";
      input.style.opacity = "0";
      document.body.appendChild(input);
      input.focus();
      input.select();
      const success = document.execCommand("copy");
      document.body.removeChild(input);
      if (success) {
        setCopied(true);
        setTimeout(() => setCopied(false), 3000);
      }
    } catch { /* fallback failed */ }
  };

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
        <span>کد کالا:</span>
        <b dir="ltr">{product.sku || product.code}</b>
      </div>
    </div>
  );
}
