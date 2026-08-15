"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { forgotPassword, requestOtp, verifyOtp } from "../../../lib/api/auth";
export default function ForgotPasswordPage() {
  const router = useRouter();
  const [identifier, setIdentifier] = useState(""); const [method, setMethod] = useState<"email" | "otp" | null>(null); const [code, setCode] = useState(""); const [message, setMessage] = useState(""); const [error, setError] = useState("");
  const submit = async (event: React.FormEvent) => { event.preventDefault(); setError(""); try { const data = await forgotPassword<{ method: "email" | "otp"; detail: string }>({ identifier }); setMethod(data.method); setMessage(data.detail); if (data.method === "otp") await requestOtp({ phone_number: identifier, purpose: "password_reset" }); } catch (reason) { setError(reason instanceof Error ? reason.message : "درخواست ناموفق بود."); } };
  const verify = async (event: React.FormEvent) => { event.preventDefault(); try { const data = await verifyOtp<{ detail: string; reset_token?: string }>({ phone_number: identifier, code, purpose: "password_reset" }); if (data.reset_token) router.push(`/fa/reset-password?reset_token=${encodeURIComponent(data.reset_token)}`); else setMessage(data.detail); } catch (reason) { setError(reason instanceof Error ? reason.message : "درخواست ناموفق بود."); } };
  return <main className="auth-page"><section className="auth-panel"><header><span>بازیابی امن</span><h1>فراموشی رمز عبور</h1><p>ایمیل یا شماره موبایل حساب خود را وارد کنید.</p></header>{method === "otp" ? <form className="auth-form" onSubmit={verify}><label>کد یکبار مصرف<input value={code} onChange={(e) => setCode(e.target.value)} inputMode="numeric" dir="ltr" maxLength={6} required /></label><button className="auth-primary">تأیید کد</button></form> : <form className="auth-form" onSubmit={submit}><label>ایمیل یا شماره موبایل<input value={identifier} onChange={(e) => setIdentifier(e.target.value)} dir="ltr" required /></label><button className="auth-primary">ادامه</button></form>}{message && <p className="auth-success">{message}</p>}{error && <p className="auth-error">{error}</p>}<p className="auth-switch"><Link href="/fa/login">بازگشت به ورود</Link></p></section></main>;
}
