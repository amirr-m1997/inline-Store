import Link from "next/link";

export default function EditorialNotFound() {
  return <main className="public-page site-container editorial-empty"><h1>مطلب پیدا نشد</h1><p>این مطلب منتشر نشده یا دیگر در دسترس نیست.</p><Link className="btn-secondary" href="/fa/knowledge">بازگشت به دانش و اخبار</Link></main>;
}
