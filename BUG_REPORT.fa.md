# گزارش بررسی پروژه، باگ‌ها و ریسپانسیو‌سازی — inline-Store

تاریخ: ۲۰۲۶-۰۸-۱۸ | برنچ: `arena/01a0144e-inline-store`

---

## ۱) خلاصه

پروژه (فرانت Next.js + بک‌اند Django/DRF) بررسی کامل شد: **۴۴ مسیر صفحه × ۸ سایز نمایشگر (۳۲۰ تا ۱۹۲۰ پیکسل)** با مرورگر واقعی (Chromium headless) پیمایش و اندازه‌گیری شد، تست‌های فرانت (۱۱۶ تست) و بک‌اند (۱۸۹ تست) اجرا شد و همهٔ موارد خراب پیدا و رفع شد. نتیجهٔ نهایی:

- ✅ هیچ صفحه‌ای در هیچ سایزی **سرریز افقی (horizontal overflow)** ندارد — حتی با غیرفعال‌کردن عمدی محافظ `overflow-x`.
- ✅ تمام صفحات و بخش‌های هدر/فوتر/هیرو از یک **کانتینر مرکزچین استاندارد** استفاده می‌کنند.
- ✅ ۱۱۶/۱۱۶ تست فرانت و ۱۸۹/۱۸۹ تست بک‌اند سبز؛ TypeScript بدون خطا.

---

## ۲) کانتینر استاندارد (درخواست اصلی شما)

### وضعیت قبلی (مشکل)

سیستم کانتینر قبلاً «یکپارچه» نشده بود و مقادیر آن با هیچ استاندارد جهانی هم‌خوانی نداشت:

| مورد | قبلاً | مشکل |
|---|---|---|
| حداکثر عرض کانتینر | `1344px` | نه استاندارد Tailwind (1280px/80rem) است و نه Bootstrap (1140/1320px) |
| فاصلهٔ کناری (gutter) موبایل | مقادیر متداخل `12/16/20/24/32px` در ۴ مدیاکوئری هم‌پوشان | رفتار غیرقابل پیش‌بینی؛ بعضی بخش‌ها 10px و بعضی 20px می‌گرفتند |
| عرض صفحات | هر صفحه مقدار خودش را داشت: `1100px` حساب کاربری، `1000px` پیش‌فاکتور، `1180px` سکشن‌های خانه، `1280px` کاتالوگ، `1344px` بقیه | صفحات با هم هم‌تراز نبودند |
| gutter کامپوننت‌ها | هدر/فوتر/هیرو/صفحه محصول/کاتالوگ هرکدام padding افقی اختصاصی (10 تا 20px) داشتند که روی gutter استاندارد می‌نشست | محتوای هدر و بدنه در یک خط عمودی قرار نمی‌گرفت |

### استاندارد اعمال‌شده (مطابق کنوانسیون جهانی Tailwind/Bootstrap)

```css
:root {
  --site-container-max: 80rem;   /* = 1280px — معادل max-w-7xl تیلویند */
  --site-container-gutter: 16px; /* موبایل */
}
@media (min-width: 640px)  { :root { --site-container-gutter: 24px; } }
@media (min-width: 1024px) { :root { --site-container-gutter: 32px; } }

.site-container, .container-page {
  box-sizing: border-box;
  width: 100%;
  max-width: var(--site-container-max);
  margin-inline: auto;                    /* مرکزچین در نمایشگرهای بزرگ */
  padding-inline: var(--site-container-gutter);
}
```

رفتار در عمل:

- **موبایل (۳۲۰px):** محتوا با ۱۶px فاصلهٔ کناری، تمام عرض قابل‌استفاده را می‌گیرد.
- **تبلت/دسکتاپ (۶۴۰px به بالا):** gutter به ۲۴px و سپس ۳۲px می‌رسد.
- **نمایشگر بزرگ (۱۴۴۰/۱۹۲۰px):** محتوا دقیقاً **۱۲۸۰px** و در **مرکز صفحه** قرار می‌گیرد (اندازه‌گیری شد: در ۱۹۲۰px حاشیهٔ چپ و راست هر دو دقیقاً ۳۲۰px است) و تمام عرض را نمی‌گیرد.

### تغییرات انجام‌شده

۱. تعریف متغیرهای استاندارد کانتینر و جایگزینی ۴ مدیاکوئری هم‌پوشان gutter با دو مدیاکوئری min-width استاندارد.
۲. حذف `max-width` و `padding` افقی اختصاصیِ کامپوننت‌ها که استاندارد را می‌شکستند:
   `.reference-main-header`، `.reference-category-nav`، `.reference-topbar`، `.site-hero`، `.footer-main`، `.footer-bottom p`، `.catalog-experience`، `.account-page`، `.account-quotation-page`، `.product-detail-page`، `.enterprise-section`.
   (padding عمودی هر بخش دست‌نخورده ماند.)
۳. تراز شدن کامل هدر/منوی دسته‌بندی/هیرو/مزایا/فوتر با بدنهٔ صفحات (همه در یک خط عمودی مشترک).
۴. حذف میان‌بُرهای `overflow-x: hidden` روی `.site-hero`, `.enterprise-home`, `.category-directory` که سرریزهای واقعی را پنهان می‌کردند.

---

## ۳) باگ‌های پیدا و رفع‌شده

### ۳-۱) سرریز افقی گالری صفحهٔ محصول در تبلت (۷۶۸px)

- **مشکل:** `.gallery-stage` در عرض ۷۶۸px به‌خاطر ترکیب `aspect-ratio` + `min-height:400px` عرض خودش را ۴۶۰px محاسبه می‌کرد و ۳۸px از لبهٔ چپ صفحه بیرون می‌زد (`scrollWidth=806` در برابر `768`). این سرریز قبلاً توسط `body{overflow-x:hidden}` پنهان می‌شد.
- **رفع:** `width:100%; min-width:0` روی `.gallery-stage` (عرض حالا همیشه از ستون گرید پیروی می‌کند).

### ۳-۲) تست‌های قرمز (suite خراب) در فرانت

- **مشکل:** بعد از تغییر dropdown مرتب‌سازی کاتالوگ از `<select>` به dropdown سفارشی، دو تست `mobile-catalog.test.tsx` همچنان دنبال `role=combobox` می‌گشتند؛ و تست `company-experience.test.ts` انتظار `industries.slice(0, 4)` داشت در حالی که صفحه ۳ آیتم نمایش می‌دهد. نتیجه: ۳ تست قرمز روی برنچ اصلی.
- **رفع:** تست‌ها با الگوی صحیح ARIA (`button[aria-haspopup="listbox"]`) و تعداد واقعی آیتم‌ها به‌روز شدند.

### ۳-۳) پیکربندی دیتابیس بک‌اند (باک جدی deployment)

- **مشکل:** `docker-compose.yml` سرویس PostgreSQL می‌سازد و به آن `depends_on` دارد، اما `settings.py` بدون قید و شرط SQLite فایلی استفاده می‌کرد. یعنی در Docker همیشه داده در SQLite (داخل کانتینر) نوشته می‌شد و Postgres کاملاً بلااستفاده بود؛ داده با هر rebuild از بین می‌رفت.
- **رفع:** انتخاب DB بر اساس متغیرهای محیطی: اگر `POSTGRES_DB`/`POSTGRES_HOST` تنظیم باشد → PostgreSQL؛ در غیر این صورت SQLite فایلی؛ و پشتیبانی از `SQLITE_PATH=:memory:` (که در README وعده داده شده بود ولی پیاده نشده بود). `docker-compose.yml` و `.env.example` هم به‌روز شدند.

### ۳-۴) پیکربندی Redis در Docker

- **مشکل:** پیش‌فرض `REDIS_URL` به `localhost:6379` اشاره می‌کرد؛ در کانتینرهای Docker سرویس Redis با هاست‌نیم `redis` در دسترس است و worker سلری بدون تنظیم `.env` از کار می‌افتاد (CACHES با `IGNORE_EXCEPTIONS` خطا را پنهان می‌کرد).
- **رفع:** مستندسازی و مقداردهی در `.env.example` (`REDIS_URL=redis://redis:6379/0`) و تنظیمات compose.

### ۳-۵) CORS — آدرس آزمایشی باقی‌مانده

- **مشکل:** `CORS_ALLOWED_ORIGINS` شامل یک URL تونل آزمایشی `trycloudflare` بود که اصولاً بعد از هر ری‌استارت تونل منقضی می‌شود.
- **رفع:** حذف و جایگزینی با پورت‌های لوکال مستند.

### ۳-۶) ناهماهنگی gutter کامپوننت‌ها

مقادیر اختصاصی 10/12/14/16/18/20px در هدر، فوتر، هیرو، صفحات حساب، کاتالوگ و محصول (بخش ۲) حذف و همه روی استاندارد ۱۶/۲۴/۳۲px یکسان شدند.

---

## ۴) یافته‌های باقی‌مانده (توصیه‌ها — عمداً دست نزدم)

این موارد باگ بحرانی نیستند ولی برای کیفیت production لازم‌اند:

1. **۸ اخطار ESLint — `<img>` خام:** در `brands`, `capabilities`, `industries`, `knowledge/[slug]`, `editorial.tsx`, `search-results.tsx` از تگ img مستقیم استفاده می‌شود (اثر منفی روی LCP و بهینه‌سازی تصویر). پیشنهاد: مهاجرت به `next/image` با `unoptimized` یا افزودن remotePatterns.
2. **کد مرده:**
   - کامپوننت `components/catalog/mega-menu.tsx` تعریف شده ولی هیچ‌جا رندر نمی‌شود.
   - کامپوننت `storefront-demo.tsx` (دموی قدیمی LOCAL_SHOP) در هیچ صفحه‌ای استفاده نمی‌شود.
   - بلوک‌های CSS قدیمی (`.site-header`, `.hero`, `.home-section`, `.promo`, `.featured-products`, `.site-footer`, `.industrial-intro`, `.product-overview`, …) که کلاس‌هایشان دیگر در JSX وجود ندارند.
3. **Dockerfile فرانت:** بدون `CMD` است (تصویر standalone بالا نمی‌آید و فقط در compose با `command` override کار می‌کند) و `EXPOSE 3001` با نگاشت `3000:3000` در compose ناهماهنگ است؛ همچنین `npm install` بهتر است `npm ci` شود.
4. **امنیت deployment:** `SECRET_KEY` پیش‌فرض و `DEBUG=True` پیش‌فرض — قبل از استقرار واقعی باید env اجباری شوند. `ALLOWED_HOSTS` پیش‌فرض فقط localhost است.
5. **تحویل ایمیل/پیامک:** به‌صورت پیش‌فرض غیرفعال است (آگاهانه و امن است؛ فقط یادآوری می‌کنم که در production باید `NOTIFICATIONS_REAL_DELIVERY_ENABLED` همراه با SMTP/SMS واقعی فعال شود).
6. **`body { overflow-x: hidden }`:** به‌عنوان محافظ نهایی نگه داشته شد؛ با توجه به نتیجهٔ سوییپ (صفر سرریز در همهٔ سایزها) اکنون حذف آن هم امن است، ولی برای احتیاط مقابل محتوای وارداتیِ بلند (مثلاً تصاویر یا متن‌های بدون شکستن) باقی ماند.

---

## ۵) روش و نتایج راستی‌آزمایی

| چک | نتیجه |
|---|---|
| سوییپ ریسپانسیو (۴۴ مسیر × ۸ ویوپورت: 320/375/430/768/1024/1280/1440/1920) با محافظ overflow غیرفعال | **۰ صفحهٔ سرریز** |
| مرکزچین‌بودن کانتینر در ۱۹۲۰px | عرض دقیقاً ۱۲۸۰px، حاشیهٔ چپ=راست=۳۲۰px |
| تست‌های فرانت (Vitest) | ۱۱۶/۱۱۶ پاس |
| تست‌های بک‌اند (Django) | ۱۸۹/۱۸۹ پاس |
| TypeScript (`tsc --noEmit`) | بدون خطا |
| ESLint | ۰ خطا، ۸ اخطار (img) |

### فایل‌های تغییرکرده

- `frontend/app/globals.css` — سیستم کانتینر استاندارد + رفع سرریز گالری + حذف gutterهای متضاد و overflow-hide‌های باند-اِید
- `frontend/tests/mobile-catalog.test.tsx`، `frontend/tests/company-experience.test.ts` — به‌روزرسانی تست‌های ناسازگار
- `backend/config/settings.py` — انتخاب DB از env (Postgres / SQLite / `SQLITE_PATH`)
- `.env.example` — مستندسازی POSTGRES_*، REDIS_URL، SQLITE_PATH
- `docker-compose.yml` — تزریق متغیرهای Postgres به کانتینر backend
