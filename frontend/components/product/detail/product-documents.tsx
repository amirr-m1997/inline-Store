import type { ProductDetail, ProductDocument, DocumentType } from "../../../lib/product/types";

const labels: Record<DocumentType, string> = { datasheet: "دیتاشیت", manual: "راهنما", cad: "فایل CAD", certificate: "گواهی‌نامه", catalogue: "کاتالوگ", other: "سند فنی" };

function formatSize(size?: number) {
  if (size === undefined || size === null) return null;
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function DocumentRow({ document }: { document: ProductDocument }) {
  const size = formatSize(document.size);
  return <li className="product-document-item"><div className="product-document-info"><span className="product-document-type">{labels[document.type]}</span><strong>{document.title}</strong><small>{document.fileName || ""}{document.revision ? ` · Rev. ${document.revision}` : ""}{document.language ? ` · ${document.language}` : ""}{size ? ` · ${size}` : ""}</small></div><a className="product-document-download" href={document.fileUrl} download={document.fileName || undefined} target="_blank" rel="noreferrer" aria-label={`دانلود ${document.title}`}>دانلود <span aria-hidden="true">↓</span></a></li>;
}

export function ProductDocuments({ product }: { product: ProductDetail }) {
  const grouped = new Map<DocumentType, ProductDocument[]>(); product.documents.forEach((document) => grouped.set(document.type, [...(grouped.get(document.type) || []), document]));
  return <section className="product-documents" aria-labelledby="product-documents-title"><header><div><span>مرجع فنی محصول</span><h2 id="product-documents-title">اسناد فنی</h2></div>{product.documents.length > 0 && <small>{product.documents.length.toLocaleString("fa-IR")} سند</small>}</header>{grouped.size ? <div className="product-document-groups">{Array.from(grouped.entries()).map(([type, documents]) => <section key={type} aria-labelledby={`document-group-${type}`}><h3 id={`document-group-${type}`}>{labels[type]}</h3><ul>{documents.map((document) => <DocumentRow key={document.id} document={document} />)}</ul></section>)}</div> : <p className="empty-section">سند فنی برای این کالا ثبت نشده است.</p>}</section>;
}
