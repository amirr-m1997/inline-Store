/* MEHRASL interactive prototype. All operations are local; no data is transmitted. */
(() => {
  'use strict';
  const DATA = window.MEHRASL_DATA;
  if (!DATA || !Array.isArray(DATA.products)) {
    document.getElementById('product-grid').innerHTML = '<p>فایل داده نمونه بارگذاری نشده است. فایل‌های پروژه را کنار هم نگه دارید.</p>';
    return;
  }
  const asset = path => (window.MEHRASL_ASSETS && window.MEHRASL_ASSETS[path]) || path;
  const products = DATA.products;
  products.forEach(p => { p.image = asset(p.image); });
  const categories = DATA.categories;
  const byId = new Map(products.map(p => [p.id, p]));
  const $ = s => document.querySelector(s);
  const $$ = s => [...document.querySelectorAll(s)];
  const nf = new Intl.NumberFormat('fa-IR');
  const fa = n => nf.format(n);
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const iconPaths = {
    'search':'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
    'search-check':'<circle cx="10.5" cy="10.5" r="7"/><path d="m7 10 2 2 4-4m3.5 8.5L21 21"/>',
    'bag':'<path d="M5 7h14l1 14H4L5 7Z"/><path d="M8 8V6a4 4 0 0 1 8 0v2"/>',
    'cart-plus':'<path d="M3 3h2l3 12h10l3-8H6M10 4v6m-3-3h6"/><circle cx="9" cy="20" r="1"/><circle cx="18" cy="20" r="1"/>',
    'heart':'<path d="M20.8 4.7a5.2 5.2 0 0 0-7.4 0L12 6.1l-1.4-1.4a5.2 5.2 0 0 0-7.4 7.4L12 21l8.8-8.9a5.2 5.2 0 0 0 0-7.4Z"/>',
    'user':'<circle cx="12" cy="7" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
    'menu':'<path d="M4 6h16M4 12h16M4 18h16"/>',
    'grid':'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    'arrow-left':'<path d="M20 12H4m6-6-6 6 6 6"/>',
    'arrow-right':'<path d="M4 12h16m-6-6 6 6-6 6"/>',
    'arrow-up':'<path d="M12 20V4m-6 6 6-6 6 6"/>',
    'chevron-down':'<path d="m6 9 6 6 6-6"/>',
    'chevron-left':'<path d="m15 6-6 6 6 6"/>',
    'spark':'<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3Z"/><path d="M20 2v4m-2-2h4"/>',
    'headset':'<path d="M3 13v-2a9 9 0 0 1 18 0v6a4 4 0 0 1-4 4h-3"/><rect x="2" y="10" width="4" height="8" rx="2"/><rect x="18" y="10" width="4" height="8" rx="2"/><path d="M11 21h3"/>',
    'box':'<path d="m12 2 9 5v10l-9 5-9-5V7l9-5Zm0 10v10M3 7l9 5 9-5M7 4.8l9 5.1v4.6"/>',
    'truck':'<path d="M2 4h12v13H2V4Zm12 5h4l4 5v3h-8"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="18" r="3"/>',
    'file':'<path d="M14 2H5v20h14V7l-5-5ZM14 2v5h5M8 12h8M8 16h6"/>',
    'check':'<path d="m5 12 4 4L19 6"/>',
    'check-circle':'<circle cx="12" cy="12" r="9"/><path d="m7 12 3 3 7-7"/>',
    'x':'<path d="m6 6 12 12M18 6 6 18"/>',
    'plus':'<path d="M12 5v14M5 12h14"/>',
    'minus':'<path d="M5 12h14"/>',
    'compare':'<path d="M8 3v18M16 3v18M4 7l4-4 4 4m0 10 4 4 4-4"/>',
    'rotate':'<path d="M3 10a9 9 0 1 1 2 8M3 4v6h6"/>',
    'sort':'<path d="M7 3v18m-4-4 4 4 4-4M14 4h7m-7 5h5m-5 5h3"/>',
    'info':'<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
    'home':'<path d="m3 10 9-8 9 8v11h-6v-7H9v7H3V10Z"/>',
    'building':'<path d="M4 22V3h11v19M15 9h5v13M2 22h20M8 7h3M8 11h3M8 15h3M8 19h3"/>',
    'snowflake':'<path d="M12 2v20M3.3 7l17.4 10M3.3 17 20.7 7M9 4l3 3 3-3M9 20l3-3 3 3M3 10l4-1-1-4M18 19l-1-4 4-1M6 19l1-4-4-1M21 10l-4-1 1-4"/>',
    'compressor':'<path d="M5 6h14v13H5V6ZM7 6V3h5v3M19 10h3v6h-3M8 19v3m8-3v3M8 10h7M8 13h7M8 16h7"/>',
    'fan':'<circle cx="12" cy="12" r="2"/><path d="M10 10C1 11 2 3 8 3c5 0 5 3 4 7M14 12c7-6 11 2 7 6-3 4-6 2-8-4M11 14c1 9-8 8-9 3-1-5 3-6 8-5"/>',
    'layers':'<path d="m12 2 10 5-10 5L2 7l10-5Zm-10 10 10 5 10-5M2 17l10 5 10-5"/>',
    'valve':'<path d="M2 10h5v8H2v-8Zm15 0h5v8h-5v-8ZM7 12h10v4H7M12 12V5M7 5h10M7 3v4m10-4v4"/>',
    'circuit':'<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 2v4m6-4v4M9 18v4m6-4v4M2 9h4m-4 6h4m12-6h4m-4 6h4"/>',
    'pipe':'<path d="M3 3h7v7h4V7h7v14h-7v-4H3V3ZM1 3h11M21 5v18M14 5v18"/>',
    'water':'<path d="M12 2C9 7 4 10 4 15a8 8 0 0 0 16 0c0-5-5-8-8-13Z"/><path d="M8 15a4 4 0 0 0 4 4"/>',
    'settings':'<path d="m9 3 1-1h4l1 4 3 1 3-1 2 4-3 3v2l2 3-3 3-3-1-3 1-1 3H8l-1-4-3-1-2-4 2-3V9L2 6l3-3 4 1" transform="translate(0 -1) scale(.95)"/><circle cx="12" cy="12" r="3"/>',
    'tools':'<path d="m14 5 3 3 4-4a6 6 0 0 1-7 8L5 21l-3-3 9-9a6 6 0 0 1 8-7l-5 3Z"/>',
    'shield':'<path d="m12 2 9 4v6c0 6-9 10-9 10S3 18 3 12V6l9-4Z"/><path d="m8 12 3 3 5-6"/>',
    'clock':'<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/>',
    'camera':'<path d="M8 5l2-3h4l2 3h5v16H3V5h5Z"/><circle cx="12" cy="13" r="4"/>',
    'download':'<path d="M12 3v12m-5-5 5 5 5-5M3 16v5h18v-5"/>',
    'trash':'<path d="M3 6h18M8 6V3h8v3M5 6l1 15h12l1-15M9 10v7m6-7v7"/>'
  };
  const icon = name => `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${iconPaths[name] || iconPaths.box}</svg>`;
  function fillIcons(root = document) { root.querySelectorAll('i[data-icon]').forEach(el => { el.outerHTML = icon(el.dataset.icon); }); }
  function normalize(s) {
    return String(s).toLowerCase().replace(/ي|ى/g,'ی').replace(/ك/g,'ک')
      .replace(/[۰-۹]/g,c=>String('۰۱۲۳۴۵۶۷۸۹'.indexOf(c))).replace(/[٠-٩]/g,c=>String('٠١٢٣٤٥٦٧٨٩'.indexOf(c)))
      .replace(/[\s\u200c\u200e\u200f\-_/،.,؛]/g,'');
  }
  const storageKey = 'mehrasl-prototype-v1';
  let cart = {}, favorites = new Set(), comparison = new Set();
  let storageAvailable = true;
  try {
    const old = JSON.parse(localStorage.getItem(storageKey) || '{}');
    if (old.cart && typeof old.cart === 'object') Object.entries(old.cart).forEach(([id,q])=>{
      const p=byId.get(id); if(p && p.mode==='buy' && p.stock>0 && Number.isFinite(q) && q>0) cart[id]=Math.min(p.stock,Math.floor(q));
    });
    if (Array.isArray(old.favorites)) favorites = new Set(old.favorites.filter(id=>byId.has(id)));
  } catch (_) { storageAvailable=false; }
  function save() { try { localStorage.setItem(storageKey,JSON.stringify({cart,favorites:[...favorites]})); } catch (_) { storageAvailable=false; } }
  const state = { tab:'all', category:'all', leaf:null, query:'', onlyStock:false, sort:'default', visible:10, favoritesOnly:false };
  const discount = p => p.oldPrice && p.price < p.oldPrice ? Math.round((1-p.price/p.oldPrice)*100) : 0;
  const getCat = id => categories.find(c=>c.id===id);
  function getLeaf(id) { for (const c of categories) for (const g of c.groups) { const l=g.items.find(i=>i.id===id); if(l)return l; } return null; }
  function toast(text, error=false) {
    const el=document.createElement('div'); el.className='toast'+(error?' error':''); el.innerHTML=icon(error?'info':'check-circle')+`<span>${esc(text)}</span>`;
    $('#toast-stack').append(el); setTimeout(()=>el.remove(),3800);
  }
  function card(p) {
    let label = p.condition==='کارکرده' ? '<span class="card-label used">کارکرده</span>' : p.mode==='quote' ? '<span class="card-label quote">استعلامی</span>' : !p.stock ? '<span class="card-label unavailable">ناموجود</span>' : p.isNew ? '<span class="card-label new">جدید</span>' : p.featured ? '<span class="card-label">منتخب مهراصل</span>' : '<span class="card-label">نمونه فروشگاه</span>';
    const old = discount(p) ? `<div class="old-price-row"><span class="discount-pill">${fa(discount(p))}٪</span><del>${fa(p.oldPrice)}</del></div>` : '<div class="old-price-row"></div>';
    const price = p.mode==='quote' ? '<div class="quote-price">استعلام قیمت</div>' : `${old}<div class="price-line">${fa(p.price)}<small>تومان</small></div>`;
    const stock = p.mode==='quote' ? 'بررسی فنی پیش از سفارش' : p.stock ? `${fa(p.stock)} ${esc(p.unit)} موجود در نمونه` : 'ناموجود در داده نمونه';
    const button = p.mode==='quote' ? `<button class="card-add" data-quote="${p.id}" aria-label="درخواست قیمت نمونه برای ${esc(p.title)}">${icon('file')}</button>` : `<button class="card-add" data-add="${p.id}" ${!p.stock?'disabled':''} aria-label="افزودن ${esc(p.title)} به سبد نمونه">${icon('plus')}</button>`;
    return `<article class="product-card" data-product="${p.id}">
      <div class="card-top">${label}</div>
      <button class="heart-control${favorites.has(p.id)?' active':''}" data-favorite="${p.id}" aria-label="علاقه‌مندی: ${esc(p.title)}" aria-pressed="${favorites.has(p.id)}">${icon('heart')}</button>
      <button class="product-image-button" data-product-detail="${p.id}" aria-label="مشاهده جزئیات نمونه ${esc(p.title)}"><img src="${p.image}" alt="نمای گرافیکی نمونه ${esc(p.title)}؛ عکس کالای واقعی نیست" width="600" height="440" loading="lazy"></button>
      <div class="product-brand">${esc(p.brand)}</div><h3 class="product-title"><button data-product-detail="${p.id}">${esc(p.title)}</button></h3>
      <div class="product-model">${esc(p.model)}</div><div class="product-features">${p.features.map(s=>`<span>${esc(s)}</span>`).join('')}</div>
      <div class="product-stock${!p.stock?' no-stock':''}"><span class="stock-dot"></span>${stock}</div>
      <div class="card-price-area">${button}<div class="card-price">${price}</div></div>
      <div class="card-bottom"><button class="compare-control${comparison.has(p.id)?' active':''}" data-compare="${p.id}" aria-pressed="${comparison.has(p.id)}">${icon('compare')} مقایسه</button><span>اطلاعات نمایشی</span></div>
    </article>`;
  }
  function matchesQuery(p,q) {
    const n=normalize(q); if(!n)return true;
    const searchable=[p.title,p.brand,p.model,p.id,p.condition,getCat(p.category).title,...p.features,...p.specs.flat()].join(' ');
    return normalize(searchable).includes(n);
  }
  function filteredProducts() {
    const ps=products.filter(p=>(state.category==='all'||p.category===state.category)&&(!state.leaf||p.leaf===state.leaf)&&matchesQuery(p,state.query)&&(!state.onlyStock||p.stock>0)&&(!state.favoritesOnly||favorites.has(p.id))&&
      (state.tab==='all'||state.tab==='featured'&&p.featured||state.tab==='new'&&p.isNew||state.tab==='discount'&&discount(p)>0||state.tab==='used'&&p.condition==='کارکرده'));
    if(state.sort==='price-asc')ps.sort((a,b)=>(a.price??Infinity)-(b.price??Infinity));
    if(state.sort==='price-desc')ps.sort((a,b)=>(b.price??-Infinity)-(a.price??-Infinity));
    if(state.sort==='discount')ps.sort((a,b)=>discount(b)-discount(a));
    if(state.sort==='new')ps.sort((a,b)=>Number(b.isNew)-Number(a.isNew));
    return ps;
  }
  function renderCatalog() {
    const ps=filteredProducts(); const shown=ps.slice(0,state.visible);
    $('#product-grid').innerHTML=shown.length?shown.map(card).join(''):`<div class="empty-state">${icon('search')}<h3>${state.leaf?'برای این زیرگروه هنوز محصول نمونه‌ای نداریم.':'محصولی با این فیلترها پیدا نشد.'}</h3><p>این نسخه فقط ۲۰ کالای نمایشی دارد. نبود نتیجه، به معنی ناموجود بودن کالا در انبار مهراصل نیست.</p><button class="button button-primary" data-action="reset-catalog">دیدن همه ۲۰ محصول</button><button class="button button-light" data-action="open-quote">درخواست راهنمایی نمونه</button></div>`;
    $('#results-count').textContent=`${fa(shown.length)} از ${fa(ps.length)} محصول نمونه`;
    $('#load-more').hidden=ps.length<=state.visible;
    $('#catalog-title').textContent=state.leaf?getLeaf(state.leaf).title:state.category!=='all'?getCat(state.category).title:state.favoritesOnly?'محصولات مورد علاقه شما':'محصولات فروشگاه';
    $$('.product-tabs button').forEach(b=>{b.classList.toggle('active',b.dataset.tab===state.tab);b.setAttribute('aria-selected',String(b.dataset.tab===state.tab));});
    $('#category-select').value=state.category; $('#sort-select').value=state.sort; $('#stock-only').checked=state.onlyStock;
    const chips=[];
    if(state.query)chips.push(`<button class="active-filter" data-clear="query">جست‌وجو: ${esc(state.query)} ${icon('x')}</button>`);
    if(state.leaf)chips.push(`<button class="active-filter" data-clear="leaf">${esc(getLeaf(state.leaf).title)} ${icon('x')}</button>`);
    if(state.favoritesOnly)chips.push(`<button class="active-filter" data-clear="favoritesOnly">فقط علاقه‌مندی‌ها ${icon('x')}</button>`);
    $('#active-filters').innerHTML=chips.join('');$('#active-filters').hidden=!chips.length;
  }
  function scrollCatalog(){ $('#catalog').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'}); }
  function resetCatalog(scroll=false) {
    Object.assign(state,{tab:'all',category:'all',leaf:null,query:'',onlyStock:false,sort:'default',visible:10,favoritesOnly:false});$('#main-search').value='';renderCatalog();if(scroll)scrollCatalog();
  }
  function navigateCategory(cat, leaf=null) {
    closeMenus(); closeMobile(); Object.assign(state,{category:cat,leaf,tab:'all',query:'',visible:10,favoritesOnly:false,onlyStock:false});$('#main-search').value='';renderCatalog();scrollCatalog();
  }
  function navigateTab(tab) { closeMenus();Object.assign(state,{category:'all',leaf:null,tab,query:'',visible:10,favoritesOnly:false,onlyStock:false});$('#main-search').value='';renderCatalog();scrollCatalog(); }
  function renderHeaderCounts() {
    const count=Object.values(cart).reduce((a,b)=>a+b,0);
    $('#cart-count').textContent=fa(count);$('#mobile-cart-count').textContent=fa(count);
    $('#favorite-count').textContent=fa(favorites.size);$('#favorite-count').hidden=!favorites.size;
    $$('[data-favorite]').forEach(b=>{b.classList.toggle('active',favorites.has(b.dataset.favorite));b.setAttribute('aria-pressed',String(favorites.has(b.dataset.favorite)));});
    $$('[data-compare]').forEach(b=>{b.classList.toggle('active',comparison.has(b.dataset.compare));b.setAttribute('aria-pressed',String(comparison.has(b.dataset.compare)));});
    $('#compare-tray').hidden=!comparison.size;$('#compare-count').textContent=`${fa(comparison.size)} محصول برای مقایسه`;
    document.body.classList.toggle('has-compare',!!comparison.size);
  }
  function toggleFavorite(id) { if(!byId.has(id))return; const active=!favorites.has(id);active?favorites.add(id):favorites.delete(id);save();renderHeaderCounts();toast(active?'به علاقه‌مندی‌ها اضافه شد.':'از علاقه‌مندی‌ها حذف شد.'); if($('#main-dialog').open&&$('#dialog-body').dataset.view==='favorites')showFavorites();if(state.favoritesOnly)renderCatalog(); }
  function addToCart(id) {
    const p=byId.get(id);if(!p||p.mode==='quote')return;
    if(!p.stock){toast('این کالا در داده نمونه موجود نیست.',true);return;}
    if((cart[id]||0)>=p.stock){toast('تعداد انتخابی به سقف موجودی نمونه رسیده است.',true);return;}
    cart[id]=(cart[id]||0)+1;save();renderHeaderCounts();if($('#cart-dialog').open)renderCart();toast('محصول به سبد خرید نمونه اضافه شد.');
  }
  function changeQty(id,change) {
    const p=byId.get(id);if(!p||!cart[id])return;
    const q=cart[id]+change;
    if(q>p.stock){toast('بیش از موجودی نمونه قابل انتخاب نیست.',true);return;}
    if(q<=0)delete cart[id];else cart[id]=q;
    save();renderHeaderCounts();renderCart();
  }
  function cartTotals() { let total=0,saving=0,count=0;for(const[id,q]of Object.entries(cart)){const p=byId.get(id);total+=p.price*q;saving+=Math.max(0,(p.oldPrice||p.price)-p.price)*q;count+=q;}return{total,saving,count}; }
  function renderCart() {
    const entries=Object.entries(cart);
    $('#cart-items').innerHTML=entries.length?entries.map(([id,q])=>{const p=byId.get(id);return `<div class="cart-item"><img src="${p.image}" alt="نمای گرافیکی ${esc(p.title)}"><div><h3>${esc(p.title)}</h3><small>${esc(p.model)}</small><div class="line-price">${fa(p.price*q)} <span>تومان</span></div><div class="quantity-control"><button data-qty="${id}" data-change="-1" aria-label="کاهش تعداد ${esc(p.title)}">${icon('minus')}</button><span>${fa(q)}</span><button data-qty="${id}" data-change="1" aria-label="افزایش تعداد ${esc(p.title)}">${icon('plus')}</button></div></div><button class="icon-button" data-remove="${id}" aria-label="حذف ${esc(p.title)} از سبد">${icon('trash')}</button></div>`;}).join(''):`<div class="empty-state">${icon('bag')}<h3>سبد نمونه شما خالی است.</h3><p>از محصولات، یک یا چند قلم را به سبد اضافه کنید.</p><button class="button button-primary" data-action="cart-to-products">دیدن محصولات</button></div>`;
    const{total,saving,count}=cartTotals();
    $('#cart-summary').hidden=!entries.length;
    $('#cart-summary').innerHTML=`<div class="cart-total-row"><span>تعداد اقلام انتخابی</span><strong>${fa(count)}</strong></div><div class="cart-total-row savings"><span>مجموع تخفیف نمونه</span><strong>${fa(saving)} تومان</strong></div><div class="cart-total-row total"><span>جمع کالاها</span><strong>${fa(total)} تومان</strong></div><p>هزینه ارسال و مالیات در این داده نمونه محاسبه نشده‌اند.</p><button class="button button-primary" data-action="checkout-demo">مشاهده خلاصه سفارش نمونه ${icon('arrow-left')}</button><p>پرداخت، رزرو موجودی و ثبت سفارش واقعی انجام نمی‌شود.</p>`;
  }
  function lockBody(){document.body.style.overflow=$$('dialog[open]').length?'hidden':'';}
  function closeMain(){ $('#main-dialog').close();lockBody(); }
  function closeCart(){ $('#cart-dialog').close();lockBody(); }
  function closeMobile(){ if($('#mobile-dialog').open)$('#mobile-dialog').close();lockBody(); }
  function openMain(title,content,view='info'){
    closeMenus();closeCart();closeMobile(); const d=$('#main-dialog'); $('#dialog-title').textContent=title;$('#dialog-body').innerHTML=content;$('#dialog-body').dataset.view=view;fillIcons(d);if(!d.open)d.showModal();d.scrollTop=0;lockBody();
  }
  function openCart(){closeMenus();closeMain();closeMobile();renderCart();$('#cart-dialog').showModal();lockBody();}
  function showProduct(id) {
    const p=byId.get(id);if(!p)return; hideSuggestions();
    const condition=p.condition==='کارکرده'?'<div class="detail-note"><strong>کالای کارکرده — نمونه:</strong> گزارش سلامت، عیوب و شرایط ضمانت واقعی هنوز ارائه نشده است. هیچ تأیید سلامت واقعی در این پیش‌نمایش وجود ندارد.</div>':'';
    const pricing=p.mode==='quote'?'<div class="detail-price">نیازمند استعلام قیمت</div>':`<div class="detail-price">${p.oldPrice?`<del>${fa(p.oldPrice)} تومان</del>`:''}${fa(p.price)} <small>تومان — قیمت نمایشی</small></div>`;
    openMain('مشاهده محصول نمونه',`<div class="dialog-product"><div class="detail-art"><img src="${p.image}" alt="نمای گرافیکی نمونه ${esc(p.title)}"><p>تصویر گرافیکی خانواده محصول؛ نه عکس کالای موجود</p></div><div class="detail-info"><span class="demo-badge">محصول نمایشی · اطلاعات فنی فرضی</span><div class="product-brand">${esc(p.brand)}</div><h3>${esc(p.title)}</h3><p class="detail-model">${esc(p.model)} &nbsp;|&nbsp; ${esc(p.id)}</p><div class="detail-note">این مدل، قیمت، موجودی و مشخصات صرفاً برای ارزیابی رابط کاربری ساخته شده‌اند و مبنای انتخاب فنی یا سفارش واقعی نیستند.</div>${condition}<table class="spec-table"><caption class="sr-only">مشخصات فنی نمونه محصول</caption><tbody>${p.specs.map(([k,v])=>`<tr><th scope="row">${esc(k)}</th><td><bdi>${esc(v)}</bdi></td></tr>`).join('')}</tbody><div class="detail-stock">${p.stock?`${fa(p.stock)} ${esc(p.unit)} موجودی فرضی`:'ناموجود در داده نمایشی'} · ${esc(p.condition)}</div>${pricing}<div class="detail-actions">${p.mode==='quote'?`<button class="button button-primary" data-quote="${id}">درخواست قیمت نمونه ${icon('file')}</button>`:p.stock?`<button class="button button-primary" data-add="${id}">افزودن به سبد نمونه ${icon('plus')}</button>`:`<button class="button button-outline" data-info="notify">درخواست اطلاع‌رسانی نمونه ${icon('info')}</button>`}<button class="button button-outline" data-compare="${id}" aria-pressed="${comparison.has(id)}">مقایسه ${icon('compare')}</button></div><p class="detail-description">${esc(p.description)}</p></div></div>`,'product');
  }
  function showFavorites(){ const ps=products.filter(p=>favorites.has(p.id));openMain('علاقه‌مندی‌های شما',ps.length?`<div class="favorites-grid">${ps.map(card).join('')}</div>`:`<div class="empty-state">${icon('heart')}<h3>هنوز محصولی ذخیره نکرده‌اید.</h3><p>با لمس قلب روی کارت هر محصول، آن را به این فهرست اضافه کنید.</p><button class="button button-primary" data-action="close-dialog">بازگشت به فروشگاه</button></div>`,'favorites'); }
  function toggleCompare(id){
    if(!byId.has(id))return;
    if(comparison.has(id)){comparison.delete(id);toast('از فهرست مقایسه حذف شد.');}else{if(comparison.size>=3){toast('در این پیش‌نمایش حداکثر ۳ محصول را مقایسه کنید.',true);return;}comparison.add(id);toast('به فهرست مقایسه اضافه شد.');}
    renderHeaderCounts();
  }
  function showCompare(){
    if(comparison.size<2){toast('برای مقایسه حداقل دو محصول انتخاب کنید.',true);return;}
    const ps=[...comparison].map(id=>byId.get(id));const keys=[...new Set(ps.flatMap(p=>p.specs.map(s=>s[0])))];
    const rows=[['مدل',p=>esc(p.model)],['دسته محصول',p=>esc(getCat(p.category).short)],['قیمت نمونه',p=>p.price?`${fa(p.price)} تومان`:'استعلامی'],['موجودی نمونه',p=>`${fa(p.stock)} ${esc(p.unit)}`],['وضعیت نمونه',p=>esc(p.condition)],...keys.map(k=>[k,p=>esc((p.specs.find(s=>s[0]===k)||[])[1]||'—')])];
    openMain('مقایسه محصولات نمونه',`<p class="detail-note">مشخصات این جدول فرضی هستند. ویژگی‌های غیرهم‌نوع با «—» نمایش داده می‌شوند؛ این جدول توصیه جایگزینی فنی نیست.</p><div class="compare-scroll"><table class="compare-table"><thead><tr><th scope="col">مشخصه</th>${ps.map(p=>`<th scope="col"><img src="${p.image}" alt="نمای گرافیکی ${esc(p.title)}"><h3>${esc(p.title)}</h3><button class="button button-light" data-product-detail="${p.id}">جزئیات نمونه</button></th>`).join('')}</tr></thead><tbody>${rows.map(([label,fn])=>`<tr><th scope="row">${esc(label)}</th>${ps.map(p=>`<td><bdi>${fn(p)}</bdi></td>`).join('')}</tr>`).join('')}</tbody></table></div>`,'comparison');
  }
  function showQuote(id=null,kind='project') {
    const p=byId.get(id);const title=kind==='part'?'راهنمای شناسایی قطعه':'درخواست پیش‌فاکتور نمونه';
    openMain(title,`<div class="info-content"><span class="demo-badge">فرم آزمایشی؛ بدون ارسال یا ذخیره اطلاعات تماس</span><h3>${kind==='part'?'از مدل و کد قطعه شروع کنیم.':'نیاز خریدتان را مشخص کنید.'}</h3><p>${kind==='part'?'این فرم، مسیر پیشنهادی دریافت مدل، کد و تصویر پلاک را نشان می‌دهد. هیچ قطعه‌ای به‌صورت خودکار سازگار تشخیص داده نمی‌شود.':'فرم زیر برای نمایش روند دریافت درخواست از مشتری سازمانی یا پروژه‌ای است.'}</p></div><form class="quote-form" id="quote-form"><div class="form-warning">اطلاعات واقعی و محرمانه وارد نکنید. فرم فقط در مرورگر اعتبارسنجی می‌شود؛ هیچ درخواست، فایل یا اطلاعاتی به سرور نمی‌رود.</div><div class="form-field"><label for="quote-name">نام آزمایشی <span aria-hidden="true">*</span></label><input id="quote-name" name="name" required maxlength="70" placeholder="مثلاً: کاربر نمونه" autocomplete="off"></div><div class="form-field"><label for="quote-company">نام شرکت / پروژه</label><input id="quote-company" name="company" maxlength="100" placeholder="شرکت نمونه" autocomplete="off"></div><div class="form-field"><label for="quote-product">محصول یا مدل موردنظر <span aria-hidden="true">*</span></label><input id="quote-product" name="product" value="${p?esc(p.title):''}" required maxlength="150" placeholder="نام کالا یا کد مدل" autocomplete="off"></div><div class="form-field"><label for="quote-qty">تعداد موردنیاز</label><input id="quote-qty" name="qty" type="number" min="1" max="99999" step="1" value="1" inputmode="numeric"></div><div class="form-field full"><label for="quote-description">توضیح درخواست</label><textarea id="quote-description" name="description" maxlength="1200" placeholder="شرایط پروژه، مدل دستگاه یا اطلاعات موردنیاز را به‌صورت آزمایشی بنویسید."></textarea></div>${kind==='part'?`<div class="form-field full"><label for="quote-image">تصویر نمونه پلاک یا قطعه (اختیاری)</label><input id="quote-image" name="attachment" type="file" accept="image/jpeg,image/png,image/webp"><span class="form-caption">فایل خوانده یا بارگذاری نمی‌شود؛ فقط انتخاب فایل را شبیه‌سازی می‌کند.</span></div>`:''}<div class="form-actions"><button class="button button-primary" type="submit">ثبت درخواست آزمایشی ${icon('arrow-left')}</button></div></form>`,'quote');
    $('#quote-form').addEventListener('submit',e=>{
      e.preventDefault();const form=e.currentTarget;if(!form.reportValidity())return;
      openMain('نتیجه درخواست نمونه',`<div class="success-state">${icon('check-circle')}<h3>فرم آزمایشی با موفقیت بررسی شد.</h3><p>این فقط شبیه‌سازی رابط کاربری است. هیچ درخواستی برای مهراصل ارسال نشده و اطلاعات فرم ذخیره نشده است.</p><div class="success-ref">DEMO-RFQ-1001</div><br><button class="button button-primary" data-action="close-dialog">بازگشت به فروشگاه</button></div>`,'success');
    });
  }
  function showCheckout(){
    const entries=Object.entries(cart);if(!entries.length){toast('سبد نمونه خالی است.',true);return;}
    const t=cartTotals();
    openMain('خلاصه سفارش نمایشی',`<div class="info-content"><span class="demo-badge">این پیش‌فاکتور یا سفارش رسمی نیست.</span><h3>خلاصه اقلام انتخاب‌شده</h3><table class="spec-table"><thead><tr><th>محصول</th><th>تعداد</th><th>جمع نمونه</th></tr></thead><tbody>${entries.map(([id,q])=>{const p=byId.get(id);return`<tr><td>${esc(p.title)}</td><td>${fa(q)}</td><td>${fa(p.price*q)} تومان</td></tr>`;}).join('')}</tbody></table><div class="info-highlight"><strong>جمع کالاها: ${fa(t.total)} تومان</strong><p>هزینه حمل و مالیات مشخص نشده‌اند. پرداخت، رزرو موجودی یا سفارش واقعی انجام نمی‌شود.</p></div><div class="detail-actions"><button class="button button-primary" data-action="download-cart">دریافت خلاصه نمونه (TXT) ${icon('download')}</button><button class="button button-outline" data-action="cart">بازگشت به سبد</button></div></div>`,'checkout');
  }
  function downloadCart(){
    let text='مهراصل | خلاصه سفارش نمایشی\nاین فایل سند فروش، پیش‌فاکتور یا تأیید موجودی واقعی نیست.\n\n';
    for(const[id,q]of Object.entries(cart)){const p=byId.get(id);text+=`${p.id} | ${p.title} | تعداد: ${fa(q)} | جمع نمونه: ${fa(p.price*q)} تومان\n`;}
    text+=`\nجمع اقلام: ${fa(cartTotals().total)} تومان\nارسال و مالیات محاسبه نشده‌اند.\nهیچ پرداخت یا سفارشی ثبت نشده است.\n`;
    const url=URL.createObjectURL(new Blob(['\ufeff',text],{type:'text/plain;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='MehrAsl_Demo_Order.txt';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  const info = {
    demo:['درباره این پیش‌نمایش',`<h3>یک نمونه قابل‌کلیک، نه فروشگاه عملیاتی</h3><p>این نسخه شامل ۲۰ محصول نمونه و منوی ۱۰ دسته اصلی با ۱۱۰ گروه نهایی است. ساختار منو از برگه «منوی کامل سایت» فایل <bdi>MehrAsl_New_Inventory_Screening.xlsx</bdi> گرفته شده است؛ تعداد نمونه‌های این صفحه هیچ ارتباطی با موجودی واقعی ندارد.</p><div class="info-highlight"><p><strong>همه مدل‌های DEMO، مشخصات، قیمت‌ها، درصد تخفیف و موجودی‌ها فرضی هستند.</strong> نماهای محصول، گرافیک برداری نمونه‌اند و عکس کالاهای انبار نیستند. لوگوی مهراصل از فایل ارائه‌شده شما و بدون تغییر استفاده شده است.</p></div><p>جست‌وجو، فیلتر، مرتب‌سازی، علاقه‌مندی، مقایسه و سبد خرید در مرورگر کار می‌کنند. فرم‌ها و رهگیری سفارش صرفاً نمایشی‌اند. ورود، پرداخت، ارسال پیام، استعلام انبار و رزرو کالا انجام نمی‌شود.</p><p>علاقه‌مندی و تعداد اقلام سبد، در صورت اجازه مرورگر، فقط روی همین مرورگر ذخیره می‌شوند. هیچ اطلاعات شخصی یا فایل فرم به بیرون ارسال نمی‌شود. این نسخه هیچ ابزار تحلیل یا ردیابی ندارد.</p><p>قبل از انتشار واقعی: عکس کالا، مشخصات تأییدشده، قیمت و موجودی مجاز، سیاست گارانتی و مرجوعی، اطلاعات تماس و ارتباط امن با انبار و پرداخت باید جایگزین و آزمون شوند.</p>`],
    support:['پشتیبانی فنی',`<h3>برای انتخاب مدل یا قطعه، یک مسیر روشن</h3><p>در نسخه نهایی، اطلاعات تماس تأییدشده فروش و پشتیبانی مهراصل در این قسمت قرار می‌گیرد. در این پیش‌نمایش هیچ شماره تماس یا زمان پاسخ‌گویی ساختگی درج نشده است.</p><div class="info-grid"><button data-action="part-help">${icon('search-check')}<strong>شناسایی قطعه</strong><span>مدل، شماره فنی و تصویر پلاک</span></button><button data-action="open-quote">${icon('building')}<strong>درخواست پروژه‌ای</strong><span>فرم نمونه بررسی نیاز خرید</span></button><button data-info="tracking">${icon('truck')}<strong>رهگیری نمونه</strong><span>مشاهده روند نمایشی سفارش</span></button></div>`],
    account:['حساب کاربری — نمونه',`<h3>همه خریدها و درخواست‌ها، در یک جا</h3><p>این صفحه فقط طرح اولیه حساب مشتری است و احراز هویت واقعی ندارد.</p><div class="info-grid"><button data-info="tracking">${icon('bag')}<strong>سفارش‌های من</strong><span>رهگیری یک سفارش نمایشی</span></button><button data-action="favorites">${icon('heart')}<strong>علاقه‌مندی‌ها</strong><span>محصولاتی که در این مرورگر ذخیره کرده‌اید</span></button><button data-action="open-quote">${icon('file')}<strong>پیش‌فاکتورها</strong><span>ساخت یک درخواست آزمایشی</span></button></div><p>ورود با شماره موبایل یا رمز عبور، پس از اتصال امن به سامانه واقعی پیاده‌سازی می‌شود.</p>`],
    delivery:['ارسال و تحویل',`<h3>شرایط تحویل، پیش از پرداخت</h3><p>این بخش جای نمایش روش ارسال، بسته‌بندی، هزینه حمل و بازه تحویل تأییدشده هر محصول است. برای تجهیزات حجیم، مسیر هماهنگی و استعلام حمل جدا در نظر گرفته می‌شود.</p><div class="info-highlight"><p>در این نسخه هیچ تعرفه حمل یا زمان تحویل واقعی تعریف نشده است. عبارت‌های رابط، نمونه طراحی‌اند و تعهد ارسال ایجاد نمی‌کنند.</p></div>`],
    warranty:['گارانتی و مرجوعی',`<h3>وضعیت هر کالا، با شرایط خودش</h3><p>در نسخه واقعی، کالاهای نو، کارکرده، یونیت‌های مستقل و اقلام با شکل عرضه خاص، شرایط روشن و اختصاصی خواهند داشت. مدت و پوشش گارانتی، اجزای همراه و فرایند مرجوعی باید قبل از عرضه به تأیید مهراصل برسند.</p><div class="info-highlight"><p>هیچ مدت گارانتی یا حق مرجوعی ساختگی در این پیش‌نمایش وعده داده نشده است. اطلاعات حقوقی و تجاری پس از تأیید شرکت درج می‌شوند.</p></div>`],
    dealers:['شبکه فروش و خدمات',`<h3>ارتباط فروشگاه با شبکه مهراصل</h3><p>این صفحه جای اطلاعات تأییدشده نمایندگان، مراکز فروش و خدمات است. نام، آدرس یا شماره تماس نمونه به‌عنوان اطلاعات واقعی نمایش داده نشده است.</p><button class="button button-primary" data-action="open-quote">مشاهده فرم درخواست نمونه</button>`],
    about:['درباره فروشگاه مهراصل',`<h3>از تجهیزات کامل تا قطعات و ملزومات</h3><p>این پیش‌نمایش برای صفحه اول فروشگاه تخصصی مهراصل طراحی شده است. هدف چیدمان، دسترسی ساده به دستگاه‌ها، قطعات، مشخصات، وضعیت کالا و مسیر خرید یا درخواست قیمت است.</p><p>هویت بصری بر پایه لوگوی ارائه‌شده و ترکیب سبز، نارنجی، خاکستری و زمینه روشن شکل گرفته است. داده‌های تجاری این نسخه ساختگی‌اند.</p>`],
    privacy:['حریم خصوصی پیش‌نمایش',`<h3>این نسخه اطلاعاتی به سرور نمی‌فرستد.</h3><p>فرم‌ها درخواست شبکه ندارند. اطلاعات نام، شرکت، متن درخواست و فایل انتخاب‌شده ذخیره یا بارگذاری نمی‌شوند. داده واقعی یا محرمانه وارد فرم نمونه نکنید.</p><p>فقط شناسه محصولات مورد علاقه و تعداد اقلام سبد، در صورت فعال‌بودن فضای ذخیره مرورگر، به‌صورت محلی نگه داشته می‌شوند. نسخه بدون دسترسی به فضای ذخیره نیز تا هنگام بازبودن صفحه کار می‌کند.</p><button class="button button-outline" data-action="reset-local">پاک‌کردن علاقه‌مندی‌ها و سبد همین نمونه ${icon('trash')}</button>`],
    notify:['اطلاع‌رسانی موجودی — نمونه',`<h3>این قابلیت در نسخه واقعی به سرویس پیام متصل می‌شود.</h3><p>در این پیش‌نمایش شماره تماس دریافت نمی‌شود و پیامکی ارسال نخواهد شد. محصول ناموجود را می‌توانید به علاقه‌مندی‌های همین مرورگر اضافه کنید.</p>`],
    articles:['مرکز راهنما — نمونه',`<h3>ساختار پیشنهادی محتوای آموزشی</h3><p>سه کارت صفحه اول، جایگاه مقاله‌های انتخاب دستگاه، شناسایی قطعه و خرید کالای کارکرده را نشان می‌دهند. متن کامل و تأییدشده مقالات در این نسخه قرار نگرفته است.</p><div class="info-grid"><button data-guide="fancoil">${icon('snowflake')}<strong>انتخاب دستگاه</strong><span>فن‌کویل و اطلاعات پیش از خرید</span></button><button data-guide="part">${icon('compressor')}<strong>شناسایی قطعه</strong><span>مدل و شماره فنی</span></button><button data-guide="used">${icon('settings')}<strong>کالای کارکرده</strong><span>وضعیت و شکل عرضه</span></button></div>`]
  };
  function showInfo(key){
    if(key==='tracking'){showTracking();return;}
    const entry=info[key]||info.demo;openMain(entry[0],`<div class="info-content">${entry[1]}</div>`,'info');
  }
  function showGuide(kind){
    const titles={fancoil:'برای انتخاب فن‌کویل، از کجا شروع کنیم؟',part:'مدل و شماره فنی؛ کلید انتخاب قطعه درست',used:'در خرید کالای کارکرده چه چیزهایی روشن باشد؟'};
    const texts={fancoil:'در نسخه نهایی، ورودی‌های موردنیاز انتخاب دستگاه، تفاوت شکل‌های نصب و شیوه خواندن مشخصات تأییدشده توضیح داده می‌شود.',part:'در نسخه نهایی، محل دریافت مدل و شماره فنی، روش جست‌وجو و مسیر درخواست تأیید سازگاری توضیح داده می‌شود.',used:'در نسخه نهایی، وضعیت واقعی، عیوب اعلام‌شده، گزارش سلامت، اجزای همراه و شرایط عرضه توضیح داده می‌شود.'};
    openMain('پیش‌نمایش راهنمای فنی',`<div class="info-content"><span class="demo-badge">محتوای پیشنهادی؛ مقاله فنی نهایی نیست</span><h3>${titles[kind]||titles.part}</h3><p>${texts[kind]||texts.part}</p><div class="article-placeholder"><strong>محل قرارگیری محتوای تأییدشده مهندسی</strong>این نسخه برای تأیید چیدمان کارت و مسیر دسترسی به راهنماست. محتوای فنی واقعی و توصیه انتخاب محصول باید با نظر مرجع فنی شرکت تکمیل شود.</div><button class="button button-primary" data-action="part-help">دیدن فرم راهنمایی نمونه ${icon('arrow-left')}</button></div>`,'article');
  }
  function showTracking(){
    openMain('پیگیری سفارش — نمونه',`<div class="info-content"><span class="demo-badge">بدون اتصال به سفارش‌های واقعی</span><h3>روند پیگیری را امتحان کنید.</h3><p>برای مشاهده سناریوی نمایشی، کد <bdi>DEMO-1001</bdi> را وارد کنید.</p><form id="tracking-form" class="quote-form"><div class="form-field full"><label for="tracking-code">کد سفارش نمونه</label><input id="tracking-code" dir="ltr" value="DEMO-1001" required maxlength="30" autocomplete="off"></div><div class="form-actions"><button class="button button-primary" type="submit">مشاهده وضعیت نمونه</button></div></form><div id="tracking-result" aria-live="polite"></div></div>`,'tracking');
    $('#tracking-form').addEventListener('submit',e=>{e.preventDefault();const value=$('#tracking-code').value.trim().toUpperCase();$('#tracking-result').innerHTML=value==='DEMO-1001'?'<div class="info-highlight"><strong>سناریوی نمایشی: سفارش در مرحله آماده‌سازی</strong><p>ثبت درخواست ← بررسی سفارش ← آماده‌سازی ← تحویل به حمل</p><p>این مسیر فقط نمونه رابط است؛ سفارشی ثبت یا ارسال نشده است.</p></div>':'<div class="detail-note">این کد در داده نمایشی تعریف نشده است. کد نمونه DEMO-1001 را امتحان کنید.</div>';});
  }
  function renderMenus(){
    $('#category-grid').innerHTML=categories.map(c=>`<button class="category-tile" data-category-go="${c.id}"><span class="category-art"><img src="${asset('assets/images/'+c.art+'.svg')}" alt="" width="600" height="440" loading="lazy"></span><strong>${esc(c.short)}</strong><small>${fa(products.filter(p=>p.category===c.id).length)} محصول نمونه</small></button>`).join('');
    $('#category-select').innerHTML='<option value="all">تمام دسته‌بندی‌ها</option>'+categories.map(c=>`<option value="${c.id}">${esc(c.title)}</option>`).join('');
    $('#mega-sidebar').innerHTML=categories.map((c,i)=>`<button class="mega-category${!i?' active':''}" data-mega-cat="${c.id}" aria-pressed="${!i}">${icon(c.icon)}<span>${esc(c.title)}</span>${icon('chevron-left')}</button>`).join('');
    renderMegaDetail(categories[0].id);
    $('#mobile-categories').innerHTML=categories.map(c=>`<details class="mobile-category"><summary>${icon(c.icon)}${esc(c.title)}${icon('chevron-down')}</summary><div><button class="see-category" data-category-go="${c.id}">دیدن محصولات نمونه این دسته</button>${c.groups.map(g=>`<h4>${esc(g.title)}</h4>${g.items.map(l=>`<button data-leaf-go="${l.id}" data-parent="${c.id}">${esc(l.title)}</button>`).join('')}`).join('')}</div></details>`).join('');
  }
  function renderMegaDetail(id){
    const c=getCat(id);if(!c)return;
    $$('.mega-category').forEach(b=>{b.classList.toggle('active',b.dataset.megaCat===id);b.setAttribute('aria-pressed',String(b.dataset.megaCat===id));});
    $('#mega-detail').innerHTML=`<div class="mega-top"><h3>${esc(c.title)}</h3><button class="text-link" data-category-go="${c.id}">دیدن نمونه‌های این دسته ${icon('arrow-left')}</button></div><div class="mega-columns">${c.groups.map(g=>`<section class="mega-group"><h4>${esc(g.title)}</h4>${g.items.map(l=>`<button data-leaf-go="${l.id}" data-parent="${c.id}">${esc(l.title)}</button>`).join('')}</section>`).join('')}</div><p class="mega-note">ساختار کامل منو برای ارزیابی طراحی نمایش داده شده است؛ فقط بعضی زیرگروه‌ها محصول نمونه دارند.</p>`;
  }
  let menuHoverTimer;
  function openMega(){if(innerWidth<=700){openMobile();return;}hideSuggestions();$('#mega-menu').hidden=false;$('#menu-scrim').hidden=false;$('#category-trigger').setAttribute('aria-expanded','true');}
  function closeMenus(){clearTimeout(menuHoverTimer);$('#mega-menu').hidden=true;$('#menu-scrim').hidden=true;$('#category-trigger').setAttribute('aria-expanded','false');}
  function openMobile(){closeMenus();closeMain();closeCart();$('#mobile-dialog').showModal();lockBody();}
  function hideSuggestions(){ $('#search-suggestions').hidden=true;$('#main-search').setAttribute('aria-expanded','false'); }
  let suggestionActive=-1;
  function suggest(){const q=$('#main-search').value.trim();suggestionActive=-1;if(!q){hideSuggestions();return;}closeMenus();const ps=products.filter(p=>matchesQuery(p,q)).slice(0,6);$('#search-suggestions').innerHTML=ps.length?'<p class="suggestion-title">محصولات نمونه مرتبط</p>'+ps.map(p=>`<button class="suggestion" data-product-detail="${p.id}"><img src="${p.image}" alt=""><span><b>${esc(p.title)}</b><span>${esc(p.model)}</span></span></button>`).join(''):`<p class="search-empty">محصول نمونه‌ای پیدا نشد. نام کوتاه‌تر یا برند را امتحان کنید.</p>`;$('#search-suggestions').hidden=false;$('#main-search').setAttribute('aria-expanded','true');}
  $('#main-search').addEventListener('input',suggest);
  $('#main-search').addEventListener('keydown',e=>{
    const options=$$('.suggestion');if(e.key==='Escape'){hideSuggestions();return;}
    if((e.key==='ArrowDown'||e.key==='ArrowUp')&&options.length){e.preventDefault();suggestionActive=(suggestionActive+(e.key==='ArrowDown'?1:-1)+options.length)%options.length;options.forEach((el,i)=>el.classList.toggle('key-active',i===suggestionActive));options[suggestionActive].scrollIntoView({block:'nearest'});}
    if(e.key==='Enter'&&suggestionActive>=0&&options[suggestionActive]){e.preventDefault();options[suggestionActive].click();}
  });
  $('#search-form').addEventListener('submit',e=>{e.preventDefault();const q=$('#main-search').value.trim();Object.assign(state,{category:'all',leaf:null,query:q,tab:'all',visible:10,favoritesOnly:false,onlyStock:false});hideSuggestions();closeMenus();renderCatalog();scrollCatalog();});
  $('#category-select').addEventListener('change',e=>{state.category=e.target.value;state.leaf=null;state.visible=10;renderCatalog();});
  $('#sort-select').addEventListener('change',e=>{state.sort=e.target.value;state.visible=10;renderCatalog();});
  $('#stock-only').addEventListener('change',e=>{state.onlyStock=e.target.checked;state.visible=10;renderCatalog();});
  $('#load-more').addEventListener('click',()=>{state.visible+=10;renderCatalog();});
  $('#reset-filters').addEventListener('click',()=>resetCatalog(false));
  $('#category-trigger').addEventListener('click',()=>$('#mega-menu').hidden?openMega():closeMenus());
  if(matchMedia('(hover:hover)').matches){$('.category-trigger-wrap').addEventListener('mouseenter',()=>{menuHoverTimer=setTimeout(openMega,170);});$('.category-trigger-wrap').addEventListener('mouseleave',()=>clearTimeout(menuHoverTimer));$('#mega-menu').addEventListener('mouseleave',()=>{menuHoverTimer=setTimeout(closeMenus,250);});$('#mega-menu').addEventListener('mouseenter',()=>clearTimeout(menuHoverTimer));}
  $('#mega-sidebar').addEventListener('mouseover',e=>{const b=e.target.closest('[data-mega-cat]');if(b)renderMegaDetail(b.dataset.megaCat);});
  $('#mega-sidebar').addEventListener('focusin',e=>{const b=e.target.closest('[data-mega-cat]');if(b)renderMegaDetail(b.dataset.megaCat);});
  $('#menu-scrim').addEventListener('click',closeMenus);
  $$('dialog').forEach(d=>{d.addEventListener('close',lockBody);d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}});});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeMenus();hideSuggestions();}});
  document.addEventListener('click',e=>{
    if(!e.target.closest('.search-wrap'))hideSuggestions();
    const b=e.target.closest('button,a');if(!b)return;
    const d=b.dataset;
    if(d.productDetail){showProduct(d.productDetail);return;}
    if(d.add){addToCart(d.add);return;}
    if(d.favorite){toggleFavorite(d.favorite);return;}
    if(d.compare){toggleCompare(d.compare);return;}
    if(d.quote){showQuote(d.quote);return;}
    if(d.qty){changeQty(d.qty,Number(d.change));return;}
    if(d.remove){delete cart[d.remove];save();renderHeaderCounts();renderCart();return;}
    if(d.info){showInfo(d.info);return;}
    if(d.guide){showGuide(d.guide);return;}
    if(d.megaCat){renderMegaDetail(d.megaCat);return;}
    if(d.categoryGo){navigateCategory(d.categoryGo);return;}
    if(d.leafGo){navigateCategory(d.parent,d.leafGo);return;}
    if(d.tabGo){navigateTab(d.tabGo);return;}
    if(d.tab){state.tab=d.tab;state.visible=10;renderCatalog();return;}
    if(d.brand){Object.assign(state,{query:d.brand,category:'all',leaf:null,tab:'all',visible:10,favoritesOnly:false,onlyStock:false});$('#main-search').value=d.brand;renderCatalog();scrollCatalog();return;}
    if(d.clear){state[d.clear]=d.clear==='query'?'':d.clear==='leaf'?null:false;if(d.clear==='query')$('#main-search').value='';renderCatalog();return;}
    if(d.slide!==undefined){setSlide(Number(d.slide));return;}
    const actions={
      'cart':openCart,'favorites':showFavorites,'close-dialog':closeMain,'close-cart':closeCart,'close-mobile':closeMobile,
      'mobile-menu':openMobile,'all-categories':()=>innerWidth<=700?openMobile():openMega(),'open-quote':()=>showQuote(),
      'part-help':()=>showQuote(null,'part'),'reset-catalog':()=>resetCatalog(true),'cart-to-products':()=>{closeCart();resetCatalog(true);},
      'ready':()=>{resetCatalog();state.onlyStock=true;renderCatalog();scrollCatalog();},
      'compare':showCompare,'clear-compare':()=>{comparison.clear();renderHeaderCounts();},'checkout-demo':showCheckout,'download-cart':downloadCart,
      'reset-local':()=>{cart={};favorites.clear();comparison.clear();save();renderHeaderCounts();renderCatalog();toast('اطلاعات محلی این پیش‌نمایش پاک شد.');},
      'next-slide':()=>setSlide((currentSlide+1)%3)
    };
    if(d.action&&actions[d.action])actions[d.action]();
  });
  const slides=[
    {title:'انتخاب دقیق.<br><span>خرید مطمئن.</span>',description:'تجهیزات و قطعات تهویه و تبرید، در یک مسیر روشن؛<br class="desktop-only"> از انتخاب فنی تا تأمین نیاز پروژه شما.',art:'chiller',small:'compressor-green',text:'انتخاب بر اساس مدل و کد',cta:'مشاهده محصولات'},
    {title:'قطعه درست؛<br><span>برای کارِ درست.</span>',description:'کمپرسور، موتور، کنترلر و قطعات مدار تبرید؛<br class="desktop-only"> جست‌وجو و مقایسه را از مشخصات شروع کنید.',art:'compressor-green',small:'axial',text:'جست‌وجوی تخصصی قطعات',cta:'دیدن قطعات نمونه'},
    {title:'موجودی منتخب.<br><span>فرصت خرید بهتر.</span>',description:'تجهیزات و قطعات منتخب در بخش پیشنهادهای ویژه؛<br class="desktop-only"> وضعیت و شرایط هر کالا را کنار قیمت ببینید.',art:'fancoil',small:'copper',text:'لوله و ملزومات نصب',cta:'مشاهده تخفیف‌ها'}
  ];
  let currentSlide=0;
  function setSlide(index){currentSlide=index;const s=slides[index];$('#hero-title').innerHTML=s.title;$('#hero-description').innerHTML=s.description;$('#hero-art').src=asset(`assets/images/${s.art}.svg`);$('#hero-small-art').src=asset(`assets/images/${s.small}.svg`);$('#hero-small-text').textContent=s.text;$('#hero-cta').innerHTML=esc(s.cta)+icon('arrow-left');$('#slide-index').textContent=String(index+1).padStart(2,'0').replace(/[0-9]/g,c=>'۰۱۲۳۴۵۶۷۸۹'[c]);$$('[data-slide]').forEach(b=>{b.classList.toggle('active',Number(b.dataset.slide)===index);b.setAttribute('aria-pressed',String(Number(b.dataset.slide)===index));});}
  $('#hero-cta').addEventListener('click',e=>{e.preventDefault();if(currentSlide===2)navigateTab('discount');else if(currentSlide===1)navigateCategory('B');else resetCatalog(true);});
  renderMenus();
  $('#special-products').innerHTML=['DEMO-005','DEMO-006','DEMO-015','DEMO-019'].map(id=>card(byId.get(id))).join('');
  $('#latest-products').innerHTML=['DEMO-013','DEMO-017','DEMO-010','DEMO-002','DEMO-011'].map(id=>card(byId.get(id))).join('');
  renderCatalog();renderHeaderCounts();fillIcons();
  // Keyboard navigation for the tablist. No auto-rotating banners or fake urgency.
  $('.product-tabs').addEventListener('keydown',e=>{
    if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;
    const tabs=$$('.product-tabs button');const ix=tabs.indexOf(document.activeElement);if(ix<0)return;
    e.preventDefault();let next=e.key==='Home'?0:e.key==='End'?tabs.length-1:(ix+(e.key==='ArrowLeft'?1:-1)+tabs.length)%tabs.length;
    tabs[next].focus();tabs[next].click();
  });
  // Expose read-only diagnostics for integration/testing, not for live commerce.
  window.MEHRASL_PREVIEW = Object.freeze({version:'1.0',productCount:products.length,categoryCount:categories.length,leafCount:categories.reduce((n,c)=>n+c.groups.reduce((m,g)=>m+g.items.length,0),0),isDemo:true});
})();
