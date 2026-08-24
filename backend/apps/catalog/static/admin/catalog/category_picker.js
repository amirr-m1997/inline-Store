(() => {
  const initialise = () => {
  const dialog = document.createElement('dialog');
  dialog.className = 'category-picker-dialog';
  dialog.innerHTML = `
    <form method="dialog" class="category-picker-dialog__head"><h2>انتخاب دسته‌بندی</h2><button class="category-picker-dialog__close" aria-label="بستن">×</button></form>
    <div class="category-picker-dialog__body">
      <input class="category-picker-dialog__search" type="search" placeholder="جست‌وجو با نام یا کد دسته‌بندی" autocomplete="off">
      <div class="category-picker-dialog__crumbs" aria-label="مسیر دسته‌بندی"></div>
      <div class="category-picker-dialog__list" aria-live="polite"></div>
    </div>`;
  document.body.appendChild(dialog);

  const search = dialog.querySelector('.category-picker-dialog__search');
  const crumbs = dialog.querySelector('.category-picker-dialog__crumbs');
  const list = dialog.querySelector('.category-picker-dialog__list');
  let activePicker = null;
  let trail = [];
  let searchTimer = null;

  const currentSelect = () => activePicker?.querySelector('select');
  const queryUrl = (parameters = {}) => {
    const url = new URL(activePicker.dataset.pickerUrl, window.location.origin);
    const excluded = activePicker.dataset.excludeIds;
    if (excluded) url.searchParams.set('exclude', excluded);
    Object.entries(parameters).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') url.searchParams.set(key, value);
    });
    return url;
  };
  const selectedText = (select) => select.options[select.selectedIndex]?.text || '';
  const updatePicker = (picker) => {
    const select = picker.querySelector('select');
    const value = picker.querySelector('[data-category-picker-value]');
    value.textContent = select.value ? selectedText(select) : 'دسته‌بندی اصلی / بدون والد';
  };
  const choose = (item) => {
    const select = currentSelect();
    select.value = String(item.id);
    select.dispatchEvent(new Event('change', { bubbles: true }));
    updatePicker(activePicker);
    dialog.close();
  };
  const renderCrumbs = () => {
    crumbs.replaceChildren();
    const root = document.createElement('button');
    root.type = 'button'; root.className = 'category-picker-dialog__crumb'; root.textContent = 'دسته‌های اصلی';
    root.addEventListener('click', () => { trail = []; search.value = ''; load(); });
    crumbs.appendChild(root);
    trail.forEach((item, index) => {
      const crumb = document.createElement('button');
      crumb.type = 'button'; crumb.className = 'category-picker-dialog__crumb'; crumb.textContent = item.name;
      crumb.addEventListener('click', () => { trail = trail.slice(0, index + 1); search.value = ''; load(); });
      crumbs.appendChild(crumb);
    });
  };
  const renderItems = (items) => {
    list.replaceChildren();
    if (!items.length) {
      const empty = document.createElement('p'); empty.className = 'category-picker-dialog__empty'; empty.textContent = 'دسته‌ای پیدا نشد.'; list.appendChild(empty); return;
    }
    items.forEach((item) => {
      const row = document.createElement('div'); row.className = 'category-picker-dialog__item';
      const main = document.createElement('button'); main.type = 'button'; main.className = 'category-picker-dialog__item-main';
      const name = document.createElement('strong'); name.textContent = item.name;
      const code = document.createElement('small'); code.textContent = item.code;
      main.append(name, code); main.addEventListener('click', () => { if (item.has_children) { trail.push(item); search.value = ''; load(); } else { choose(item); } }); row.appendChild(main);
      const select = document.createElement('button'); select.type = 'button'; select.className = 'category-picker-dialog__select'; select.textContent = 'انتخاب'; select.addEventListener('click', () => choose(item)); row.appendChild(select);
      if (item.has_children) {
        const next = document.createElement('button'); next.type = 'button'; next.className = 'category-picker-dialog__next'; next.textContent = 'زیرمجموعه‌ها';
        next.addEventListener('click', () => { trail.push(item); search.value = ''; load(); }); row.appendChild(next);
      }
      list.appendChild(row);
    });
  };
  const load = async () => {
    if (!activePicker) return;
    list.textContent = 'در حال دریافت…';
    renderCrumbs();
    const parameters = search.value.trim() ? { q: search.value.trim() } : { parent: trail.at(-1)?.id };
    try {
      const response = await fetch(queryUrl(parameters), { credentials: 'same-origin' });
      if (!response.ok) throw new Error('Unable to load categories');
      renderItems((await response.json()).results);
    } catch (_) {
      list.textContent = 'دریافت دسته‌بندی‌ها ناموفق بود. دوباره تلاش کنید.';
    }
  };
  document.addEventListener('click', (event) => {
    const openButton = event.target.closest('[data-category-picker-open]');
    if (openButton) {
      activePicker = openButton.closest('[data-category-picker]'); trail = []; search.value = ''; dialog.showModal(); load(); return;
    }
    const clearButton = event.target.closest('[data-category-picker-clear]');
    if (clearButton) {
      const picker = clearButton.closest('[data-category-picker]'); const select = picker.querySelector('select');
      select.value = ''; select.dispatchEvent(new Event('change', { bubbles: true })); updatePicker(picker);
    }
  });
  search.addEventListener('input', () => { clearTimeout(searchTimer); searchTimer = setTimeout(load, 250); });
  document.querySelectorAll('[data-category-picker]').forEach(updatePicker);
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialise, { once: true });
  } else {
    initialise();
  }
})();