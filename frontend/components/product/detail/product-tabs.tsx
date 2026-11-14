import type { ReactNode } from "react";
import DOMPurify from "isomorphic-dompurify";

// معرفی محصول و مشخصات فنی در یک صفحه، پشت سر هم با سرفصل مشخص (بدون تب).
// بخش مشخصات فنی فقط وقتی رندر می‌شود که مشخصاتی ثبت شده باشد.
export function ProductTabs({ description, specifications, hasSpecifications = true }: { description: string; specifications: ReactNode; hasSpecifications?: boolean }) {
  if (!description && !hasSpecifications) return null;
  const sanitizedDescription = description ? DOMPurify.sanitize(description) : "";

  return <section className="product-detail-tabs product-detail-tabs--single" aria-label="توضیحات و مشخصات فنی محصول">
    {description ? <>
      <h2 className="product-detail-section-title">معرفی محصول</h2>
      <div className="product-description-body" dangerouslySetInnerHTML={{ __html: sanitizedDescription }} />
    </> : null}
    {hasSpecifications ? <>
      <h2 className="product-detail-section-title">مشخصات فنی</h2>
      {specifications}
    </> : null}
  </section>;
}
