# تحلیل فاز اول — LOCAL_SHOP

## نتیجه و محدوده

این سند حاصل بررسی `LOCAL_SHOP.zip` است. دمو یک فایل مستقل HTML/JavaScript با نام `local_shop.html` است و **فقط مرجع رفتار و تجربهٔ کاربری** محسوب می‌شود؛ معماری تک‌فایلی و داده‌های درون‌جاوااسکریپت آن نباید به نسخهٔ عملیاتی منتقل شود.

طبق دستور پروژه، این مرحله صرفاً تحلیل است و هیچ پیاده‌سازی Django/Next.js انجام نشده است.

## یافته‌های قابل اتکا از دمو

| مورد | یافته |
|---|---|
| ساختار فایل | یک HTML حدود 3.4 مگابایتی، با CSS، UI، منطق و دادهٔ JSON درون یک فایل |
| دادهٔ کالا | 12,971 محصول؛ فیلدهای `code`, `name`, `unit`, `t`, `g`, `z`, `inv`, `res`, `lastReceiptDate`, `lastIssueDate`, `lastPurchaseIRRPrice`, `usdRateAtLastReceipt` |
| طبقه‌بندی | 14 نوع، 123 گروه و 697 زیرگروه؛ کدهای گروه و زیرگروه فقط در محدودهٔ نوع یکتا هستند |
| تصویر | 9 فایل JPG شامل یک placeholder (`000000.jpg`) و 8 تصویر با نام کد کالا؛ 6 نام تصویر با کد محصول موجود منطبق‌اند |
| زبان | فارسی زبان پیش‌فرض است؛ انگلیسی با فرهنگ لغت محدود/ترانویسی ساخته می‌شود؛ جهت صفحه با زبان تغییر می‌کند |
| نقاط شکست CSS | 1050، 980، 720، 640 و 560 پیکسل؛ در نمایش کوچک دسته‌بندی به drawer تبدیل می‌شود |
| ذخیره‌سازی مرورگر | زبان، نرخ روز دلار و سبد با `localStorage` ذخیره می‌شوند |

### ساختار UI و مسیرهای رفتاری

- هدر شامل برند، جست‌وجوی سریع، دکمهٔ دسته‌بندی موبایل، جست‌وجوی پیشرفته، داشبورد، سبد و تعویض زبان است.
- سایدبار راست یک درخت باز/بسته‌شوندهٔ «نوع ← گروه ← زیرگروه» با تعداد کالای زیرگروه و حالت انتخاب‌شده دارد. در موبایل همان درخت داخل drawer نمایش داده می‌شود.
- انتخاب نوع، گروه یا زیرگروه، لیست کالاها را نشان می‌دهد. breadcrumb و دکمهٔ بازگشت برای جزئیات وجود دارد.
- کارت محصول تصویر، نام، کد، واحد، موجودی، رزرو، وضعیت و کنترل `− / تعداد / +` دارد؛ کلیک روی کارت به جزئیات می‌رود.
- جزئیات محصول گالری (با fallback تصویر)، موجودی/رزرو، تاریخ آخرین رسید و حواله، آخرین قیمت خرید ریالی، نرخ دلار زمان رسید، قیمت دلاری و معادل روز را نشان می‌دهد.
- جست‌وجوی سریع با debounce 250ms، نام/کد/واحد را در حافظهٔ مرورگر جست‌وجو می‌کند؛ حداقل دو کاراکتر و سقف 100 نتیجه دارد.
- جست‌وجوی پیشرفته فیلتر نام، کد، حداقل موجودی، حداقل رزرو، بازهٔ حواله، بازهٔ رسید، «بدون حواله»، نوع، گروه، زیرگروه و مرتب‌سازی تاریخ حواله/موجودی/رزرو را ارائه می‌کند.
- سبد عملیات افزودن، کاهش، حذف، پاک‌کردن، شمارش ردیف و مجموع تعداد دارد و CSV با اطلاعات کالا، موجودی، رزرو و محاسبات ارزی صادر می‌کند.
- داشبورد KPIهای تعداد کالا/نوع/گروه/زیرگروه و کالاهای دارای موجودی و رزرو را محاسبه می‌کند؛ همچنین Top 10 موجودی، رزرو، خالص، بدون حواله و قدیمی‌ترین رسید/حواله و گروه‌بندی‌ها را نشان می‌دهد.

## مواردی که باید حفظ شوند

1. تجربهٔ RTL، ظاهر کارت‌محور روشن، سایهٔ ملایم، رنگ تأکیدی قرمز و رنگ ثانویهٔ آبی.
2. درخت دسته‌بندی، شمارندهٔ کالا، باز/بسته شدن، انتخاب فعال و drawer موبایل.
3. اطلاعات و عملیات کارت، صفحهٔ جزئیات، گالری و fallback تصویر.
4. جست‌وجوی سریع، مجموعهٔ کامل فیلترهای پیشرفته، CSV سبد و شاخص‌های داشبورد.
5. فارسی به‌عنوان زبان پیش‌فرض و امکان استفاده از `fa-IR` و `en` با RTL/LTR واقعی.
6. تاریخ‌های شمسی در نمایش کاربر، با ذخیره‌سازی استاندارد و قابل‌جست‌وجو در backend.

## مواردی که باید تغییر کند یا نباید کپی شود

- دادهٔ `DATA`، فیلتر، جست‌وجو، آمار و کل سبد فعلاً در client اجرا می‌شوند. با 12,971 کالا این روش مقیاس‌پذیر نیست و نباید ادامه یابد.
- HTML تک‌فایلی، `innerHTML` گسترده و JavaScript بدون type safety به کامپوننت‌های TypeScript و API تفکیک‌شده تبدیل شوند.
- `localStorage` فقط برای تنظیمات کم‌خطر و سبد مهمان قابل استفاده است؛ سبد کاربر واردشده باید server-side باشد و هنگام ورود merge شود.
- دمو برای داده‌های گمشده، قیمت خرید را `45000` و نرخ دلار را `1` جایگزین می‌کند. این پیش‌فرض‌ها در production خطرناک‌اند و باید به دادهٔ ناموجود/نیازمند تکمیل تبدیل شوند.
- دمو مقدار نمایشی «خالص» را `inv + res` محاسبه می‌کند. معنای دادهٔ منبع باید هنگام import تأیید شود؛ در مدل پیشنهادی، موجودی قابل فروش برابر `on_hand - reserved` است و با constraint محافظت می‌شود.
- محاسبات پولی فعلی با `Number` هستند؛ backend و API باید از `Decimal` استفاده کنند.
- تصاویر دمو فقط 6 تطابق قطعی با محصول دارند. ارتباط‌ها باید در گزارش import ثبت و موارد نامنطبق برای تعیین تکلیف نگه‌داری شوند.
- ترجمهٔ انگلیسی دمو تا حدی بر ترانویسی تکیه دارد. نسخهٔ عملیاتی باید کلیدهای ترجمهٔ بازبینی‌شده داشته باشد.

## معماری پیشنهادی

```text
Browser
  ↓
Next.js (App Router, TypeScript, Tailwind, RTL-aware i18n)
  ↓ HTTPS / REST
Django + Django REST Framework
  ↓                 ↘
PostgreSQL           Redis (cache, rate limits, Celery broker when needed)
                        ↓
                      Celery worker (imports, image processing, scheduled jobs)
```

### ساختار backend

```text
backend/
  config/
  apps/
    accounts/       # کاربر، نقش و مجوز
    catalog/        # دسته‌بندی، کالا و تصویر
    inventory/      # موجودی، رسید، حواله و رزرو
    pricing/        # تاریخچهٔ قیمت و نرخ ارز
    carts/          # سبد و آیتم‌های آن
    dashboard/      # query/serviceهای گزارش
    common/         # pagination، permissions، validation و utilities
  requirements/
```

### اصول اجرایی

- PostgreSQL منبع قطعی داده است؛ جست‌وجو، فیلتر و aggregation در DB اجرا می‌شوند.
- قرارداد API نسخه‌دار (`/api/v1/`) و مستندسازی OpenAPI/Swagger تولید می‌شود.
- تنظیمات و secrets فقط از environment variables خوانده می‌شوند؛ `.env` در Git وارد نمی‌شود.
- احراز هویت، مجوز نقش‌محور، CSRF/CORS محدود، اعتبارسنجی serializer، rate limiting و cookies امن لازم است.
- list endpointها صفحه‌بندی، ordering صریح، index مناسب و `select_related/prefetch_related` خواهند داشت.

## طرح پیشنهادی پایگاه داده

### کاتالوگ

- `Category`: `id`, `code`, `name_fa`, `name_en`, `slug`, `parent` (nullable)، `level`, `is_active`, timestamps.
  - یک مدل self-referential برای سلسله‌مراتب جایگزین سه جدول ثابت می‌شود و عمق فعلی سه‌سطحی را حفظ می‌کند.
  - unique constraint برای `(parent, code)` و `(parent, slug)`؛ مسیر/ancestorها برای query سریع نگه‌داری یا تولید می‌شوند.
- `Product`: `id`, `code` (unique/indexed), `name`, `slug`, `category` (برگ درخت), `unit`, `description`, `is_active`, timestamps.
- `ProductImage`: `product`, `image`, `alt_text`, `is_primary`, `sort_order`, timestamps؛ فایل‌ها در `/media/products/` ذخیره می‌شوند.

### انبار و گردش کالا

- `Inventory`: یک ردیف برای هر product، شامل `on_hand_quantity`, `reserved_quantity`, `updated_at`.
  - `available_quantity` property/annotation است، نه ستون قابل ویرایش مستقل.
  - check constraint: هر دو مقدار غیرمنفی و `reserved_quantity <= on_hand_quantity`.
- `Receipt`: `product`, `quantity`, `occurred_at`, `reference`, `unit_purchase_price_irr`, `usd_rate`, `created_at`.
- `Issue`: `product`, `quantity`, `occurred_at`, `reference`, `created_at`.
- `Reservation`: `product`, `cart_item` یا مرجع سفارش، `quantity`, `status`, `expires_at`, timestamps؛ تغییر آن باید در transaction موجودی رزرو شده را به‌روز کند.

### قیمت و ارز

- `ProductPrice`: `product`, `amount`, `currency`, `effective_from`, `effective_to` (nullable), `created_at`, `source`.
- `CurrencyRate`: `currency`, `rate_to_irr`, `rate_date`, `source`, timestamps؛ unique برای `(currency, rate_date)`.
- تمام مقدارهای پولی `DecimalField` هستند. نرخ/قیمت معادل امروز از آخرین قیمت معتبر و نرخ معتبر محاسبه، ثبت و منبع آن مشخص می‌شود.

### کاربر و سبد

- `User` یا user سفارشی مبتنی بر Django، به‌علاوهٔ role/group/permission.
- `Cart`: `user` (nullable برای مهمان), `guest_token` (nullable), `status`, timestamps.
- `CartItem`: `cart`, `product`, `quantity`, timestamps؛ unique برای `(cart, product)`.
- سبد مهمان با کوکی/توکن امضاشده شناخته می‌شود و در ورود، در transaction با سبد کاربر merge می‌شود.

### indexهای اولیه

- `Product(code)`, `Product(slug)`, `Product(category, is_active)`, index/GIN مناسب برای نام و کد جست‌وجویی.
- `Receipt(product, occurred_at)`, `Issue(product, occurred_at)`, `Reservation(product, status, expires_at)`.
- `ProductPrice(product, effective_from)`, `CurrencyRate(currency, rate_date)`.

## طرح API

همهٔ list endpointها `page`, `page_size`, ordering مجاز و پاسخ استاندارد صفحه‌بندی دارند.

| Endpoint | مسئولیت |
|---|---|
| `GET /api/v1/categories/` | درخت دسته‌بندی با شمارندهٔ محصولات فعال |
| `GET /api/v1/products/` | فهرست صفحه‌بندی‌شده با category، stock status و ordering |
| `GET /api/v1/products/{slug}/` | جزئیات، تصاویر، snapshot موجودی، آخرین رسید/حواله و قیمت |
| `GET /api/v1/search/?q=` | جست‌وجوی سریع server-side نام و کد |
| `GET /api/v1/products/advanced-search/` | تمام فیلترهای دمو، تاریخ‌های استاندارد ISO و sorting whitelist |
| `GET /api/v1/dashboard/` | KPI و جدول‌های Top 10؛ با cache کوتاه‌مدت |
| `GET /api/v1/currency-rates/` | نرخ‌های قابل مشاهده و نرخ جاری |
| `GET, POST, DELETE /api/v1/cart/` | دریافت/پاک‌سازی سبد و ایجاد سبد در صورت نیاز |
| `POST /api/v1/cart/items/` | افزودن کالا یا افزایش مقدار |
| `PATCH, DELETE /api/v1/cart/items/{id}/` | set quantity یا حذف با اعتبارسنجی موجودی |
| `GET /api/v1/cart/export.csv` | خروجی CSV با header امن و محاسبات مبتنی بر Decimal |
| `POST /api/v1/auth/login`, `POST /logout`, `POST /register` | جریان احراز هویت مطابق سیاست محصول |

فیلتر پیشرفته باید نام، کد، حداقل موجودی/رزرو، بازه‌های رسید و حواله، بدون حواله، category/group/subcategory و sort field/direction را با query parameterهای validate‌شده پشتیبانی کند. ورودی تاریخ شمسی در frontend به تاریخ استاندارد API تبدیل می‌شود و query هرگز بر متن تاریخ نمایش اجرا نمی‌شود.

## طرح frontend

```text
frontend/
  app/[locale]/
    page.tsx
    products/[slug]/page.tsx
    categories/[...slug]/page.tsx
    search/page.tsx
    cart/page.tsx
    dashboard/page.tsx
  components/
    layout/        # Header, SidebarTree, MobileCategoryDrawer, Footer
    catalog/       # ProductGrid, ProductCard, CategoryBreadcrumb
    product/       # ProductGallery, ProductFacts, QuantityControl
    search/        # QuickSearch, AdvancedSearchForm
    cart/          # CartList, CartItemRow, CartSummary
    dashboard/     # KpiCards, RankedProductTable
  services/        # typed API clients
  lib/             # i18n, jalali formatting, money formatting
  types/           # API/domain types
```

- App Router، TypeScript strict و Tailwind برای طراحی responsive استفاده می‌شوند.
- صفحه‌های عمومی محصول و category metadata کامل (title، description، canonical، Open Graph، JSON-LD در صورت نیاز)، `sitemap.xml` و `robots.txt` دارند.
- Server Components برای دادهٔ اولیهٔ SEO و Client Components فقط برای تعامل‌های لازم استفاده می‌شوند.
- زبان در مسیر یا cookie مدیریت می‌شود؛ `lang` و `dir` روی ریشهٔ سند قرار می‌گیرند و اعداد/تاریخ‌ها بر اساس locale قالب‌بندی می‌شوند.

## رفتار responsive و معیار پذیرش

دمو breakpointهای 1050/980/720/640/560 دارد. نسخهٔ جدید باید در 1536×864، 1366×768، 1280×720، 1024×768، 768×1024، 763×651، 430×932، 390×844 و 375×812 آزمایش شود؛ به‌خصوص 763×651. سایدبار دسکتاپ در عرض کوچک drawer است، grid بدون عرض ثابت و بدون overflow افقی ناخواسته عمل می‌کند، و کنترل تعداد/دکمه‌ها قابل لمس و قابل دسترس هستند.

## کاستی‌ها و ریسک‌های دمو برای production

1. هیچ backend، دیتابیس، transaction، authentication یا authorization ندارد.
2. تمام 12,971 کالا به مرورگر ارسال می‌شوند؛ فیلتر و dashboard در client محاسبه می‌شود.
3. pagination، caching server-side، index، query optimization و monitoring ندارد.
4. سبد localStorage اعتبار موجودی ندارد و هم‌زمانی یا merge پس از login را پوشش نمی‌دهد.
5. رسید/حواله فقط آخرین تاریخ‌های denormalized هستند؛ تاریخچهٔ قابل حسابرسی ندارند.
6. موجودی، رزرو و قواعد کمبود موجودی در transaction محافظت نمی‌شوند.
7. داده‌های ناموجود قیمت/نرخ با fallbackهای ساختگی پنهان می‌شوند.
8. ترجمهٔ انگلیسی کامل و domain-approved نیست؛ نام‌ها گاه ترانویسی می‌شوند.
9. وضعیت تصویر، image optimization، upload policy و رابطهٔ قطعی همهٔ فایل‌ها با محصول تعیین نشده است.
10. تست، Docker، CI، environment isolation، logging، backup/restore و مستندات عملیاتی ندارد.

## برنامهٔ مهاجرت داده

1. JSON درون `const DATA` به یک فایل منبع versioned استخراج می‌شود؛ checksum و گزارش تعدادها ثبت می‌گردد.
2. category tree با ترکیب `(t, g, z)` import می‌شود؛ صرفاً `g` یا `z` به‌تنهایی کلید خارجی نیست.
3. محصول‌ها با `code` upsert می‌شوند. mapping دادهٔ `inv` به `on_hand` یا `available` قبل از import نهایی با مالک داده تأیید می‌شود.
4. تصاویر بر اساس code attach، placeholder جداگانه ثبت و دو نام نامنطبق در گزارش exception ثبت می‌شوند.
5. این کار در management command idempotent مانند `python manage.py import_demo_data` انجام و با dry-run و گزارش خطا اجرا می‌شود.

## خروجی فاز اول

مرجع UI و رفتارهای ضروری مشخص شد و طراحی پیشنهادی برای فازهای بعدی (مدل‌ها، API، frontend، امنیت، تست و deployment) در همین سند ثبت گردید. مرحلهٔ بعدی فقط پس از دستور جدید، با ساختار پروژه و مدل‌های Django آغاز می‌شود.
