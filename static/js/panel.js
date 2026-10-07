/* ============================================================ panel.js
   ارتقاهای دسترس‌پذیری و تجربه‌ی کاربری پنل مهراصل (۱۴۰۵/۰۷/۱۵)
   ۱) برچسب و راهنمای کادر جست‌وجوی فهرست‌ها (aria-label + placeholder)
   ۲) برچسب دسترس‌پذیر برای چک‌باکس‌های انتخاب ردیف
   ۳) مشخص‌کردن گزینه‌ی فعال سایدبار برای صفحه‌خوان‌ها (aria-current)
   ۴) تبدیل دوطرفه‌ی تاریخ شمسی/میلادی در ورودی‌های تاریخ + راهنمای زیر فیلد
*/
(function () {
  "use strict";

  /* ---------------------------------------------------------- تبدیل تاریخ */
  var gDaysInMonth = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];

  function gregorianToJalali(gy, gm, gd) {
    var jy = gy <= 1600 ? 0 : 979;
    gy -= gy <= 1600 ? 621 : 1600;
    var gy2 = gm > 2 ? gy + 1 : gy;
    var days =
      365 * gy +
      Math.floor((gy2 + 3) / 4) -
      Math.floor((gy2 + 99) / 100) +
      Math.floor((gy2 + 399) / 400) -
      80 +
      gd +
      gDaysInMonth[gm - 1];
    jy += 33 * Math.floor(days / 12053);
    days %= 12053;
    jy += 4 * Math.floor(days / 1461);
    days %= 1461;
    if (days > 365) {
      jy += Math.floor((days - 1) / 365);
      days = (days - 1) % 365;
    }
    var jm = days < 186 ? 1 + Math.floor(days / 31) : 7 + Math.floor((days - 186) / 30);
    var jd = 1 + (days < 186 ? days % 31 : (days - 186) % 30);
    return [jy, jm, jd];
  }

  function jalaliToGregorian(jy, jm, jd) {
    var gy = jy <= 979 ? 621 : 1600;
    jy -= jy <= 979 ? 0 : 979;
    var days =
      365 * jy +
      Math.floor(jy / 33) * 8 +
      Math.floor(((jy % 33) + 3) / 4) +
      78 +
      jd +
      (jm < 7 ? (jm - 1) * 31 : (jm - 7) * 30 + 186);
    gy += 400 * Math.floor(days / 146097);
    days %= 146097;
    if (days > 36524) {
      gy += 100 * Math.floor(--days / 36524);
      days %= 36524;
      if (days >= 365) days++;
    }
    gy += 4 * Math.floor(days / 1461);
    days %= 1461;
    if (days > 365) {
      gy += Math.floor((days - 1) / 365);
      days = (days - 1) % 365;
    }
    var gd = days + 1;
    var leap = (gy % 4 === 0 && gy % 100 !== 0) || gy % 400 === 0;
    var mDays = [0, 31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    var gm;
    for (gm = 0; gm < 13 && gd > mDays[gm]; gm++) gd -= mDays[gm];
    return [gy, gm, gd];
  }

  var FA = "۰۱۲۳۴۵۶۷۸۹";
  function toFa(text) {
    return String(text).replace(/[0-9]/g, function (d) {
      return FA[+d];
    });
  }
  function toEn(text) {
    return String(text).replace(/[۰-۹٠-٩]/g, function (d) {
      var i = FA.indexOf(d);
      if (i > -1) return String(i);
      return String("٠١٢٣٤٥٦٧٨٩".indexOf(d));
    });
  }
  function pad2(n) {
    return (n < 10 ? "0" : "") + n;
  }

  /* تاریخ ورودی کاربر → [سال، ماه، روز] میلادی؛ null اگر قابل تبدیل نباشد */
  function normaliseDateValue(raw) {
    var text = toEn(String(raw || "")).trim().replace(/[.\-\\]/g, "/");
    if (!text) return null;
    if (/^\d{8}$/.test(text)) text = text.slice(0, 4) + "/" + text.slice(4, 6) + "/" + text.slice(6);
    var parts = text.split("/");
    if (parts.length !== 3) return null;
    var y = parseInt(parts[0], 10),
      m = parseInt(parts[1], 10),
      d = parseInt(parts[2], 10);
    if (!y || !m || !d || m > 12 || d > 31) return null;
    if (y >= 1200 && y <= 1599) return jalaliToGregorian(y, m, d);
    if (y >= 1700 && y <= 2200) return [y, m, d];
    return null;
  }

  /* ------------------------------------------------------ برچسب‌های دسترس‌پذیری */
  function labelSearch() {
    document.querySelectorAll('input[name="q"]:not([aria-label])').forEach(function (el) {
      el.setAttribute("aria-label", "جست‌وجو در این فهرست");
      if (!el.placeholder) el.placeholder = "جست‌وجو…";
      var form = el.closest("form");
      if (form && !form.getAttribute("role")) form.setAttribute("role", "search");
    });
    var submit = document.querySelector("#searchbar-submit");
    if (submit && !submit.getAttribute("aria-label")) submit.setAttribute("aria-label", "جست‌وجو");
  }

  function labelCheckboxes() {
    document.querySelectorAll('input[name="action-toggle"]:not([aria-label])').forEach(function (el) {
      el.setAttribute("aria-label", "انتخاب همه‌ی ردیف‌های این صفحه");
    });
    document.querySelectorAll('#result_list input[type="checkbox"][name="_selected_action"]:not([aria-label])').forEach(function (el) {
      el.setAttribute("aria-label", "انتخاب این ردیف");
    });
  }

  function markCurrentNav() {
    var path = location.pathname.replace(/\/$/, "");
    document.querySelectorAll("a[href]").forEach(function (a) {
      var href = a.getAttribute("href") || "";
      if (href.charAt(0) !== "/") return;
      var clean = href.split("?")[0].replace(/\/$/, "");
      if (clean && clean === path && !a.getAttribute("aria-current")) {
        a.setAttribute("aria-current", "page");
      }
    });
  }

  /* ------------------------------------------------- تاریخ شمسی در ورودی‌ها */
  function hintFor(input) {
    var hint = input.parentElement && input.parentElement.querySelector(".panel-jalali-hint");
    if (hint) return hint;
    hint = document.createElement("span");
    hint.className = "panel-jalali-hint";
    hint.dir = "rtl";
    input.insertAdjacentElement("afterend", hint);
    return hint;
  }

  function refreshHint(input) {
    var hint = hintFor(input);
    var iso = /^(\d{4})-(\d{2})-(\d{2})$/.exec(toEn(input.value).trim());
    if (iso) {
      var j = gregorianToJalali(+iso[1], +iso[2], +iso[3]);
      hint.textContent = "= " + toFa(j[0] + "/" + pad2(j[1]) + "/" + pad2(j[2])) + " شمسی";
      hint.className = "panel-jalali-hint panel-jalali-hint--ok";
      return;
    }
    var parsed = normaliseDateValue(input.value);
    if (parsed && /[۰-۹٠-٩]|\//.test(input.value)) {
      hint.textContent = "= " + (parsed[0] + "-" + pad2(parsed[1]) + "-" + pad2(parsed[2])) + " میلادی";
      hint.className = "panel-jalali-hint panel-jalali-hint--ok";
      return;
    }
    hint.textContent = input.value ? "قالب تاریخ: ۱۴۰۵/۰۷/۱۵ شمسی" : "";
    hint.className = "panel-jalali-hint";
  }

  function wireDateInputs() {
    document.querySelectorAll("input.vDateField").forEach(function (input) {
      if (input.dataset.panelJalali === "1") return;
      input.dataset.panelJalali = "1";
      if (!input.getAttribute("title")) {
        input.setAttribute("title", "تاریخ شمسی (۱۴۰۵/۰۷/۱۵) یا میلادی را وارد کنید");
      }
      ["input", "change", "blur"].forEach(function (evt) {
        input.addEventListener(evt, function () {
          refreshHint(input);
        });
      });
      /* پیش از ارسال فرم: ورودی شمسی → میلادی، تا سرور همیشه میلادی بگیرد */
      input.addEventListener("change", function () {
        var parsed = normaliseDateValue(input.value);
        if (!parsed) return;
        if (/^\d{4}-\d{2}-\d{2}$/.test(toEn(input.value).trim())) return;
        input.value = parsed[0] + "-" + pad2(parsed[1]) + "-" + pad2(parsed[2]);
        refreshHint(input);
      });
      refreshHint(input);
    });
  }

  /* -------------------------------------------------- ارقام فارسی در شمارنده‌ها
     شمارنده‌ی اکشن‌های گروهی، نوار صفحه‌بندی، فیلترها و «سلسله‌مراتب تاریخ»
     اعداد را لاتین نشان می‌دهند؛ اینجا فقط متن (نه attribute) فارسی می‌شود. */
  function persianizeTextNodes(root) {
    if (!root) return;
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    var node;
    while ((node = walker.nextNode())) {
      var parent = node.parentNode;
      if (!parent) continue;
      var tag = parent.nodeName;
      if (tag === "SCRIPT" || tag === "STYLE" || tag === "INPUT" || tag === "TEXTAREA") continue;
      var converted = toFa(node.nodeValue);
      if (converted !== node.nodeValue) node.nodeValue = converted;
    }
  }

  var countersBusy = false;
  function persianizeCounters() {
    if (countersBusy) return;
    countersBusy = true;
    try {
      document.querySelectorAll(".action-counter, .all, .question").forEach(persianizeTextNodes);
      document.querySelectorAll("#changelist-filter, ul.toplinks, .paginator").forEach(persianizeTextNodes);
      /* شمارنده‌های سایدبار (تعداد ردیف هر مدل) و خلاصه‌ی صفحه‌بندی */
      document.querySelectorAll("#nav-sidebar a, .paginator, .changelist-footer").forEach(
        persianizeTextNodes
      );
      document.querySelectorAll('a[href^="?p="]').forEach(function (a) {
        var bar = a.parentElement ? a.parentElement.parentElement || a.parentElement : null;
        persianizeTextNodes(bar);
      });
    } finally {
      countersBusy = false;
    }
  }

  var observer = null;
  function watchCounters() {
    if (!window.MutationObserver) return;
    var scope = document.querySelector("#changelist-form") || document.body;
    if (!scope) return;
    var timer = null;
    observer = new MutationObserver(function () {
      if (timer) clearTimeout(timer);
      timer = setTimeout(function () {
        if (observer) observer.disconnect();
        persianizeCounters();
        if (observer) observer.observe(scope, { childList: true, subtree: true, characterData: true });
      }, 40);
    });
    observer.observe(scope, { childList: true, subtree: true, characterData: true });
  }

  /* ------------------------------------------- پیوند «پرش به محتوای اصلی» (WCAG 2.4.1) */
  function addSkipLink() {
    if (document.getElementById("panel-skip-link")) return;
    var main = document.querySelector("main") || document.getElementById("content");
    if (!main) return;
    if (!main.id) main.id = "panel-main";
    if (!main.getAttribute("tabindex")) main.setAttribute("tabindex", "-1");
    var link = document.createElement("a");
    link.id = "panel-skip-link";
    link.className = "panel-skip-link";
    link.href = "#" + main.id;
    link.textContent = "پرش به محتوای اصلی";
    link.addEventListener("click", function () {
      /* فوکوس واقعی روی محتوا، تا کلید Tab از همان‌جا ادامه پیدا کند */
      setTimeout(function () { main.focus(); }, 0);
    });
    if (document.body.firstChild) document.body.insertBefore(link, document.body.firstChild);
    else document.body.appendChild(link);
  }

  /* ------------------------------------------------- میان‌بر جست‌وجو: / و Esc */
  function addSearchHint() {
    var bar = document.getElementById("searchbar") || document.querySelector("#changelist-search");
    var input = document.querySelector('input[name="q"]');
    if (!bar || !input) return;
    if (!bar.querySelector(".panel-search-hint")) {
      var hint = document.createElement("span");
      hint.className = "panel-search-hint";
      hint.innerHTML =
        '<span class="panel-kbd">/</span> جست‌وجو' +
        '<span class="panel-kbd">Esc</span> پاک‌کردن';
      bar.appendChild(hint);
    }
    if (input.dataset.panelShortcut === "1") return;
    input.dataset.panelShortcut = "1";
    input.addEventListener("keydown", function (evt) {
      if (evt.key === "Escape") {
        input.value = "";
        input.blur();
      }
    });
    document.addEventListener("keydown", function (evt) {
      if (evt.key !== "/" || evt.ctrlKey || evt.metaKey || evt.altKey) return;
      var tag = (evt.target && evt.target.tagName) || "";
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" ||
          (evt.target && evt.target.isContentEditable)) return;
      evt.preventDefault();
      input.focus();
      input.select();
    });
  }

  /* --------------------------------------- کنش‌های درون‌ردیفی فهرست‌ها (ویرایش/تاریخچه/حذف)
     لینک‌ها از خودِ لینک «تغییر» هر ردیف ساخته می‌شوند، پس همیشه به همان شیء
     اشاره می‌کنند. «حذف» تنها وقتی اضافه می‌شود که کنش گروهی حذف در همین صفحه
     موجود باشد (یعنی کاربر مجوز حذف دارد). */
  function addRowActions() {
    var list = document.getElementById("result_list");
    if (!list) return;
    var canDelete = !!document.querySelector(
      '#changelist-form select[name="action"] option[value="delete_selected"]'
    );
    var flag = String(canDelete);
    if (list.dataset.panelRowActions === flag) return;   /* بار قبل همین وضعیت بوده */
    list.dataset.panelRowActions = flag;

    var rows = list.querySelectorAll("tbody tr");
    Array.prototype.forEach.call(rows, function (row) {
      if (row.querySelector(".panel-row-actions")) return;
      var link = row.querySelector('a[href*="/change/"]');
      if (!link) return;
      var cell = link.closest("td, th") || row.firstElementChild;
      if (!cell) return;
      var base = link.getAttribute("href").split("?")[0];
      var box = document.createElement("span");
      box.className = "panel-row-actions";
      box.appendChild(actionLink(link.getAttribute("href"), "ویرایش", ""));
      box.appendChild(actionLink(base.replace("/change/", "/history/"), "تاریخچه", ""));
      if (canDelete) {
        box.appendChild(actionLink(base.replace("/change/", "/delete/"), "حذف", "panel-act-danger"));
      }
      cell.appendChild(box);
    });
  }

  function actionLink(href, label, extraClass) {
    var a = document.createElement("a");
    a.href = href;
    a.className = extraClass || "";
    a.setAttribute("aria-label", label);
    var span = document.createElement("span");
    span.className = "panel-act-label";
    span.textContent = label;
    a.appendChild(span);
    return a;
  }

  /* --------------------------------------- نوار راهنمای فهرست + شمارش انتخاب‌ها */
  function addListHint() {
    var form = document.getElementById("changelist-form");
    var list = document.getElementById("result_list");
    if (!form || !list || document.getElementById("panel-list-hint")) return;
    var hint = document.createElement("p");
    hint.id = "panel-list-hint";
    hint.className = "panel-list-hint";
    hint.setAttribute("role", "status");
    hint.setAttribute("aria-live", "polite");
    /* جدول ممکن است فرزند مستقیم فرم نباشد (unfold آن را در div می‌گذارد) */
    if (list.parentNode) list.parentNode.insertBefore(hint, list);
    else form.insertBefore(hint, form.firstChild);
    refreshListHint();

    if (form.dataset.panelHintWired === "1") return;
    form.dataset.panelHintWired = "1";
    form.addEventListener("change", function (evt) {
      if (evt.target && evt.target.name === "_selected_action") refreshListHint();
    });
    form.addEventListener("click", function (evt) {
      if (evt.target && evt.target.name === "action-toggle") refreshListHint();
    });
  }

  function refreshListHint() {
    var hint = document.getElementById("panel-list-hint");
    if (!hint) return;
    var chosen = document.querySelectorAll('#result_list input[name="_selected_action"]:checked').length;
    var total = document.querySelectorAll('#result_list input[name="_selected_action"]').length;
    hint.textContent = chosen
      ? toFa(chosen) + " ردیف انتخاب شده — از کادر «کنش» بالای فهرست استفاده کنید."
      : "برای کنش‌های گروهی ردیف‌ها را تیک بزنید؛ برای جست‌وجوی سریع کلید / را بزنید. "
        + "(" + toFa(total) + " ردیف در این صفحه)";
  }


  /* ----------------------------- راهنمای اسکرول افقی جدول‌ها (فقط اگر واقعاً سرریز باشد) */
  function addScrollHints() {
    document.querySelectorAll(".panel-card-body.panel-tight").forEach(function (box) {
      var previous = box.previousElementSibling;
      var hint = previous && previous.classList && previous.classList.contains("panel-scroll-hint")
        ? previous : null;
      var scrollable = box.scrollWidth > box.clientWidth + 4;
      if (!scrollable) {
        if (hint) hint.remove();
        return;
      }
      if (hint) return;
      var el = document.createElement("p");
      el.className = "panel-scroll-hint";
      el.setAttribute("role", "note");
      el.innerHTML = "<b>↔</b> برای دیدن ستون‌های بیشتر، جدول را افقی بکشید.";
      box.parentNode.insertBefore(el, box);
    });
  }

  /* ----------------------------- سلول چک‌باکس هم کلیک‌پذیر شود (هدف لمسی بزرگ‌تر) */
  function clickableCheckboxCells() {
    document.querySelectorAll(
      'input[type="checkbox"][name="_selected_action"], input[type="checkbox"].al-row, td.action-checkbox input, thead input[type="checkbox"]'
    ).forEach(function (box) {
      var cell = box.closest("td, th");
      if (!cell || cell.dataset.panelCellClick === "1") return;
      cell.dataset.panelCellClick = "1";
      cell.style.cursor = "pointer";
      cell.addEventListener("click", function (evt) {
        if (evt.target === box || (evt.target.closest && evt.target.closest("a, label, button"))) return;
        if (box.id === "action-toggle" || box.closest("thead")) {
          /* «انتخاب همه»: کلیک واقعی تا منطق خود جنگو هم اجرا شود */
          box.click();
          return;
        }
        box.checked = !box.checked;
        box.dispatchEvent(new Event("change", { bubbles: true }));
      });
    });
  }

  function boot() {
    try {
      labelSearch();
      labelCheckboxes();
      markCurrentNav();
      wireDateInputs();
      persianizeCounters();
      watchCounters();
      addSkipLink();
      addSearchHint();
      addRowActions();
      addListHint();
      addScrollHints();
      clickableCheckboxCells();
    } catch (e) {
      /* در صورت خطا، پنل باید دست‌نخورده کار کند */
      if (window.console && console.warn) console.warn("panel.js:", e);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
  document.addEventListener("formset:added", boot);
})();
