import Link from "next/link";

const style = `
.standalone-not-found{min-height:100vh;margin:0;display:grid;place-items:center;padding:32px 16px;background:linear-gradient(135deg,#16241c,#2d5a32 60%,#638444);font-family:Vazirmatn,Tahoma,sans-serif}
.standalone-not-found-card{width:min(100%,620px);text-align:center;padding:52px 36px;border-radius:22px;background:#f8f9f6;box-shadow:0 30px 70px rgba(0,0,0,.35)}
.standalone-not-found-code{display:block;font-size:110px;font-weight:900;line-height:1;background:linear-gradient(135deg,#2d5a32,#6da351);-webkit-background-clip:text;background-clip:text;color:transparent}
.standalone-not-found-card h1{margin:10px 0 4px;color:#1e2d24;font-size:24px}
.standalone-not-found-card p{margin:0 auto;max-width:440px;color:#56675c;font-size:13px;line-height:2}
.standalone-not-found-links{display:flex;flex-wrap:wrap;justify-content:center;gap:10px;margin-top:26px}
.standalone-not-found-links a{padding:11px 22px;border-radius:999px;text-decoration:none;font-size:13px;font-weight:800}
.standalone-not-found-links a.primary{background:#2d5a32;color:#fff}
.standalone-not-found-links a.plain{border:1px solid #c4cdc2;color:#1e2d24}
.standalone-not-found-ltr{direction:ltr}
`;

export default function NotFound() {
  return (
    <main className="standalone-not-found">
      <style>{style}</style>
      <div className="standalone-not-found-card">
        <span className="standalone-not-found-code" aria-hidden="true">404</span>
        <h1>این صفحه از خط تولید خارج شده است!</h1>
        <p>صفحه‌ای که دنبال آن هستید منتقل شده، حذف شده یا اصلاً وجود نداشته است.</p>
        <div className="standalone-not-found-links">
          <Link className="primary" href="/fa">صفحه اصلی فارسی</Link>
          <Link className="plain" href="/fa/shop">مشاهده محصولات</Link>
        </div>
        <p className="standalone-not-found-ltr" style={{ marginTop: 22 }}>The page you are looking for does not exist.</p>
        <div className="standalone-not-found-links standalone-not-found-ltr">
          <Link className="primary" href="/en">English home</Link>
          <Link className="plain" href="/en/shop">Browse products</Link>
        </div>
      </div>
    </main>
  );
}
