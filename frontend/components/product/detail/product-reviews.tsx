"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, apiRequest } from "../../../lib/api/client";
import { formatNumber } from "../../../lib/product/formatters";

type Review = { id: number; rating: number; comment: string; customer_name: string; created_at: string; is_published: boolean };
type ReviewData = { summary: { count: number; average_rating: number | null }; reviews: Review[]; can_review: boolean; viewer_review: Review | null };

const Stars = ({ value, interactive = false, onChange }: { value: number; interactive?: boolean; onChange?: (value: number) => void }) => <span className="product-review-stars" aria-label={`${value} از ۵`}>{[1, 2, 3, 4, 5].map((star) => interactive ? <button type="button" key={star} onClick={() => onChange?.(star)} className={star <= value ? "is-filled" : ""} aria-label={`${star} ستاره`}>★</button> : <i key={star} className={star <= value ? "is-filled" : ""}>★</i>)}</span>;

export function ProductReviews({ productId }: { productId: number }) {
  const [data, setData] = useState<ReviewData | null>(null);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const endpoint = `/api/v1/catalog/products/${productId}/reviews/`;
  const load = useCallback(() => apiRequest<ReviewData>(endpoint, { cache: "no-store" }).then((next) => { setData(next); if (next.viewer_review) { setRating(next.viewer_review.rating); setComment(next.viewer_review.comment); } }).catch(() => setData(null)), [endpoint]);
  useEffect(() => { load(); }, [load]);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setSubmitting(true); setMessage("");
    try { const result = await apiRequest<{ detail: string }>(endpoint, { method: "POST", body: { rating, comment } }); setMessage(result.detail); await load(); }
    catch (error) { setMessage(error instanceof ApiError ? error.message : "ثبت نظر ناموفق بود."); }
    finally { setSubmitting(false); }
  };
  return <section className="product-reviews" aria-labelledby="product-reviews-title"><header><div><span>تجربه خریداران</span><h2 id="product-reviews-title">امتیاز و نظر درباره محصول</h2></div>{data?.summary.average_rating !== null && data?.summary.average_rating !== undefined && <div className="product-review-summary"><b>{formatNumber(data.summary.average_rating)}</b><Stars value={Math.round(data.summary.average_rating)} /><small>{formatNumber(data.summary.count)} نظر ثبت‌شده</small></div>}</header>{data?.can_review ? <form onSubmit={submit} className="product-review-form"><div><b>{data.viewer_review ? "نظر خود را به‌روزرسانی کنید" : "شما این محصول را خریده‌اید؛ تجربه‌تان را ثبت کنید."}</b><Stars value={rating} interactive onChange={setRating} /></div><textarea value={comment} onChange={(event) => setComment(event.target.value)} maxLength={3000} placeholder="نظر شما درباره کیفیت، کاربری و تجربه خرید…" required /><button type="submit" disabled={submitting}>{submitting ? "در حال ثبت…" : "ثبت نظر و امتیاز"}</button>{message && <p role="status">{message}</p>}</form> : <p className="product-review-eligibility">برای ثبت نظر، ابتدا محصول را خریداری کنید. پس از ثبت سفارش، نظر شما با نام حساب کاربری ثبت می‌شود.</p>}<div className="product-review-list">{data?.reviews.length ? data.reviews.map((review) => <article key={review.id}><header><b>{review.customer_name}</b><Stars value={review.rating} /><time>{new Date(review.created_at).toLocaleDateString("en-US")}</time></header><p>{review.comment}</p></article>) : <p>هنوز نظری برای این محصول ثبت نشده است.</p>}</div></section>;
}
