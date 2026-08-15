import { Button } from "./button";

export function Pagination({ page, totalPages, onPrevious, onNext }: { page: number; totalPages: number; onPrevious: () => void; onNext: () => void }) {
  return <nav className="ui-pagination" aria-label="صفحه‌بندی"><Button variant="secondary" size="sm" onClick={onPrevious} disabled={page <= 1}>صفحه قبل</Button><span>صفحه {page.toLocaleString("fa-IR")} از {totalPages.toLocaleString("fa-IR")}</span><Button variant="secondary" size="sm" onClick={onNext} disabled={page >= totalPages}>صفحه بعد</Button></nav>;
}
