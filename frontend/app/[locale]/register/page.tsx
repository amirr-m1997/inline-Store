"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { GoogleSignIn } from "../../../components/auth/google-sign-in";
import { authChanged, mergeGuestCart } from "../../../services/auth-client";
import { register } from "../../../lib/api/auth";

export default function RegisterPage() {
  const router = useRouter(); const [password, setPassword] = useState(""); const [visible, setVisible] = useState(false); const [error, setError] = useState(""); const [loading, setLoading] = useState(false);
  const strength = useMemo(() => [password.length >= 8, /[A-Za-z]/.test(password), /\d/.test(password), /[^A-Za-z0-9]/.test(password)].filter(Boolean).length, [password]);
  const finish = async () => { await mergeGuestCart(); authChanged(); router.replace("/fa/account"); router.refresh(); };
  const submit = async (event: React.FormEvent<HTMLFormElement>) => { event.preventDefault(); setLoading(true); setError(""); try { await register(Object.fromEntries(new FormData(event.currentTarget))); await finish(); } catch (reason) { setError(reason instanceof Error ? reason.message : "درخواست ناموفق بود."); } finally { setLoading(false); } };
  return <main className="auth-page"><section className="auth-panel auth-panel-wide"><header><span>عضویت مشتریان</span><h1>ایجاد حساب کاربری</h1><p>ثبت حداقل یکی از ایمیل یا شماره موبایل کافی است.</p></header><form className="auth-form auth-grid" onSubmit={submit}><label>نام *<input name="first_name" autoComplete="given-name" required /></label><label>نام خانوادگی *<input name="last_name" autoComplete="family-name" required /></label><label>ایمیل<input name="email" type="email" dir="ltr" autoComplete="email" /></label><label>شماره موبایل<input name="phone_number" dir="ltr" inputMode="tel" autoComplete="tel" placeholder="09123456789" /></label><label className="auth-full">نام شرکت<input name="company_name" /></label>
    <label>رمز عبور *<div className="password-field"><input name="password" type={visible ? "text" : "password"} dir="ltr" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" required /><button type="button" onClick={() => setVisible((value) => !value)} aria-label={visible ? "پنهان کردن رمز عبور" : "نمایش رمز عبور"}>{visible ? "پنهان" : "نمایش"}</button></div><small className={`password-strength strength-${strength}`}>قدرت رمز: {strength < 2 ? "ضعیف" : strength < 4 ? "متوسط" : "قوی"}</small></label><label>تکرار رمز عبور *<div className="password-field"><input name="password_confirm" type={visible ? "text" : "password"} dir="ltr" autoComplete="new-password" required /><button type="button" onClick={() => setVisible((value) => !value)} aria-label={visible ? "پنهان کردن تکرار رمز عبور" : "نمایش تکرار رمز عبور"}>{visible ? "پنهان" : "نمایش"}</button></div></label>
    <button className="auth-primary auth-full" disabled={loading}>{loading ? "در حال ثبت‌نام…" : "ایجاد حساب"}</button></form>{error && <p className="auth-error">{error}</p>}<div className="auth-divider"><span>یا</span></div><GoogleSignIn label="signup_with" onSuccess={() => void finish()} /><p className="auth-switch">قبلاً ثبت‌نام کرده‌اید؟ <Link href="/fa/login">وارد شوید</Link></p></section></main>;
}
