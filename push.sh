#!/usr/bin/env bash
# راه‌انداز push مخزن مهر اصل — روی مخزن محلی کار می‌کند و کاملِ تاریخچه را می‌فرستد.
#
# استفاده:
#   bash push.sh <نشانی-مخزن> [نام-شاخهٔ-مقصد]
#   bash push.sh https://<کاربر>:<توکن>@github.com/<کاربر>/<مخزن>.git
#   bash push.sh https://<کاربر>:<توکن>@github.com/amirr-m1997/inline-Store.git arena/mehrasl-panel
#   bash push.sh --check                                   (فقط نمایش وضعیت)
#
set -euo pipefail
cd "$(dirname "$0")"
BRANCH="$(git branch --show-current)"

if [[ "${1:-}" == "--check" || -z "${1:-}" ]]; then
  echo "شاخهٔ جاری: $BRANCH"
  echo "کامیت آخر:  $(git log --oneline -1)"
  echo "ریموت فعلی: $(git remote -v | head -1 || true)"
  echo "تغییرات باقی‌مانده: $(git status --porcelain | wc -l) فایل"
  echo "ریموت نیست؟ نشانی مخزن را بدهید تا با شکل زیر push شود:"
  echo "  bash push.sh https://<کاربر>:<توکن>@github.com/<کاربر>/<مخزن>.git"
  exit 0
fi

URL="$1"
TARGET_BRANCH="${2:-$BRANCH}"
echo "→ تنظیم ریموت origin روی مخزن مقصد…"
git remote remove origin 2>/dev/null || true
git remote add origin "$URL"

echo "→ بررسی دسترسی نوشتن (dry-run) → شاخهٔ مقصد: $TARGET_BRANCH"
if ! git push --dry-run origin "$BRANCH:$TARGET_BRANCH" 2>&1 | tail -3; then
  echo "✗ push آزمایشی ناموفق بود؛ معمولاً یعنی توکن/دسترسی نوشتن وجود ندارد." >&2
  exit 1
fi

echo "→ push واقعی…"
git push origin "$BRANCH:$TARGET_BRANCH"
echo "✓ انجام شد. برای پاک‌کردن نشانی حاوی توکن از تنظیمات محلی:"
echo "  git remote set-url origin https://github.com/<کاربر>/<مخزن>.git"
