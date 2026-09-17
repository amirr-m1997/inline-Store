"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, apiRequest } from "../../../lib/api/client";

type Question = { id: number; question: string; answer: string; asked_at: string; answered_at: string; customer_name: string };

export function ProductQuestions({ productId }: { productId: number }) {
  const endpoint = `/api/v1/catalog/products/${productId}/questions/`;
  const [questions, setQuestions] = useState<Question[]>([]), [question, setQuestion] = useState(""), [message, setMessage] = useState(""), [sending, setSending] = useState(false);
  const load = useCallback(() => apiRequest<{ questions: Question[] }>(endpoint, { cache: "no-store" }).then((data) => setQuestions(data.questions)).catch(() => setQuestions([])), [endpoint]);
  useEffect(() => { load(); }, [load]);
  const submit = async (event: React.FormEvent) => { event.preventDefault(); setSending(true); setMessage(""); try { const response = await apiRequest<{ detail: string }>(endpoint, { method: "POST", body: { question } }); setQuestion(""); setMessage(response.detail); } catch (error) { setMessage(error instanceof ApiError ? error.message : "ثبت پرسش ناموفق بود."); } finally { setSending(false); } };
  return <section className="product-questions" aria-labelledby="product-questions-title"><header><span>راهنمای انتخاب</span><h2 id="product-questions-title">پرسش و پاسخ محصول</h2></header><form onSubmit={submit}><textarea value={question} onChange={(event) => setQuestion(event.target.value)} maxLength={1500} placeholder="پرسش فنی یا خرید خود را بنویسید…" required /><button type="submit" disabled={sending}>{sending ? "در حال ارسال…" : "ثبت پرسش"}</button>{message && <p role="status">{message}</p>}</form><div>{questions.length ? questions.map((item) => <article key={item.id}><b>پرسش {item.customer_name}</b><p>{item.question}</p><div><strong>پاسخ مهراصل</strong><p>{item.answer}</p></div></article>) : <p className="product-question-empty">هنوز پرسش و پاسخ تأییدشده‌ای برای این محصول ثبت نشده است.</p>}</div></section>;
}
