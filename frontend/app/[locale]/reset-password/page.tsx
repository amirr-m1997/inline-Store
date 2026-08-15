"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { resetPassword } from "../../../lib/api/auth";
function ResetPasswordForm() {
  const params = useSearchParams(); const [message, setMessage] = useState(""); const [error, setError] = useState("");
  const submit = async (event: React.FormEvent<HTMLFormElement>) => { event.preventDefault(); try { const form = Object.fromEntries(new FormData(event.currentTarget)); setMessage((await resetPassword({ ...form, uid: params.get("uid"), token: params.get("token"), reset_token: params.get("reset_token") })).detail); } catch (reason) { setError(reason instanceof Error ? reason.message : "درخواست ناموفق بود."); } };
  return <main className="auth-page"><section className="auth-panel"><header><span>امنیت حساب</span><h1>تنظیم رمز عبور جدید</h1></header>{message ? <><p className="auth-success">{message}</p><p className="auth-switch"><Link href="/fa/login">ورود به حساب</Link></p></> : <form className="auth-form" onSubmit={submit}><label>رمز عبور جدید<input name="password" type="password" dir="ltr" required /></label><label>تکرار رمز عبور<input name="password_confirm" type="password" dir="ltr" required /></label><button className="auth-primary">تغییر رمز عبور</button></form>}{error && <p className="auth-error">{error}</p>}</section></main>;
}

export default function ResetPasswordPage() {
  return <Suspense fallback={<main className="auth-page"><section className="auth-panel">در حال آماده‌سازی…</section></main>}><ResetPasswordForm /></Suspense>;
}
