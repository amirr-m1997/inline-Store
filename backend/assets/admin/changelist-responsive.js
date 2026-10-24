/* Changelist responsive cards: copy the thead labels into each body cell so the
   stacked mobile layout can render "label: value" rows without knowing any
   model. Keep in sync with the max-width:767px rules in theme.css. */
(function () {
  function labelize(scope) {
    scope.querySelectorAll("#result_list, .inline-group table").forEach(function (table) {
      var labels = Array.prototype.map.call(
        table.querySelectorAll("thead th"),
        function (th) { return th.textContent.trim().replace(/\s+/g, " "); }
      );
      if (!labels.length) return;
      table.querySelectorAll("tbody tr").forEach(function (tr) {
        Array.prototype.forEach.call(tr.children, function (cell, index) {
          if (labels[index]) cell.setAttribute("data-label", labels[index]);
        });
      });
    });
  }
  // ردیف‌های تازه‌افزوده‌شده‌ی اینلاین‌ها (دکمه‌ی «افزودن») هم برچسب بگیرند.
  function watchInlineForms() {
    if (typeof MutationObserver === "undefined") return;
    document.querySelectorAll(".inline-group").forEach(function (group) {
      new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
          if (mutation.addedNodes.length) labelize(group);
        });
      }).observe(group, { childList: true, subtree: true });
    });
  }
  document.addEventListener("DOMContentLoaded", function () {
    labelize(document);
    watchInlineForms();
  });
})();
