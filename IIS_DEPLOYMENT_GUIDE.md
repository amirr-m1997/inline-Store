# راهنمای جامع استقرار آفلاین فرانت‌اند Next.js روی Windows IIS با Node.js 20.9.0

این مستند راهنمای گام‌به‌گام استقرار فرانت‌اند فروشگاه اینترنتی بر روی سرور Windows IIS (بدون دسترسی به اینترنت) است.

---

## ۱. پیش‌نیازهای سرور IIS

1. **نصب Node.js نسخه v20.9.0 LTS:**
   - مطمئن شوید دستور `node -v` در PowerShell سرور خروجی `v20.9.0` می‌دهد.
2. **نصب ماژول IIS httpPlatformHandler:**
   - نسخه 1.2 ماژول `httpPlatformHandler` مایکروسافت را روی سرور نصب کنید.
3. **ایجاد پوشه لاگ:**
   - در مسیر ریشه سایت، یک پوشه به نام `logs` ایجاد کنید و به کاربر `IIS_IUSRS` دسترسی Write دهید تا خروجی لاگ‌های Node در آن ذخیره شود.

---

## ۲. محتویات بسته انتقالی به سرور (Offline Package)

فایل‌های زیر را پس از بیلد موفق در محیط توسعه، به سرور منتقل نمایید:

1. پوشه `.next/` (حاصل دستور `npm run build`)
2. پوشه `node_modules/` (پکیج‌های هماهنگ‌شده با Node.js 20.9.0)
3. پوشه `public/` (فایل‌های استاتیک و آیکون‌ها)
4. فایل `package.json`
5. فایل `next.config.mjs`
6. فایل `web.config`

---

## ۳. تنظیمات web.config برای IIS

فایل `web.config` در ریشه پوشه سایت قرار می‌گیرد و به شکل زیر تنظیم شده است:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="httpPlatformHandler" path="*" verb="*" modules="httpPlatformHandler" resourceType="Unspecified" requireAccess="Script" />
    </handlers>
    
    <httpPlatform 
      processPath="node.exe"
      arguments="node_modules\next\dist\bin\next start -p %HTTP_PLATFORM_PORT%"
      stdoutLogEnabled="true"
      stdoutLogFile=".\logs\stdout.log"
      startupTimeLimit="120"
      processesPerApplication="1">
      <environmentVariables>
        <environmentVariable name="NODE_ENV" value="production" />
        <environmentVariable name="PORT" value="%HTTP_PLATFORM_PORT%" />
        <environmentVariable name="BACKEND_API_URL" value="http://127.0.0.1:8000" />
        <environmentVariable name="NEXT_PUBLIC_API_URL" value="http://127.0.0.1:8000" />
      </environmentVariables>
    </httpPlatform>

    <security>
      <requestFiltering>
        <requestLimits maxAllowedContentLength="52428800" />
      </requestFiltering>
    </security>
  </system.webServer>
</configuration>
```

> **نکته:** در صورتی که مسیر `node.exe` در System PATH سرور ثبت نیست، در مشخصه `processPath` مسیر کامل آن را بنویسید (مثلاً `C:\Program Files\nodejs\node.exe`).

---

## ۴. مراحل جایگزینی فایل‌ها و راه‌اندازی در سرور آفلاین

1. **متوقف کردن Application Pool سایت در IIS:**
   ```powershell
   Stop-WebAppPool -Name "CompanyStoreFrontPool"
   ```
2. **کپی و جایگزینی فایل‌ها در پوشه سایت (مثلاً `C:\inetpub\company-store-front\`)**
3. **اطمینان از دسترسی به پوشه logs:**
   ```powershell
   icacls "C:\inetpub\company-store-front\logs" /grant "IIS_IUSRS:(OI)(CI)F"
   ```
4. **استارت مجدد Application Pool:**
   ```powershell
   Start-WebAppPool -Name "CompanyStoreFrontPool"
   ```

---

## ۵. تست و عیب‌یابی (Troubleshooting)

در صورتی که صفحه باز نشد، فایل لاگ زیر را بررسی کنید:
`.\logs\stdout.log`
این فایل تمامی خطاهای احتمالی فرآیند اجرای Node.js و پورت‌های محلی را ثبت می‌کند.
