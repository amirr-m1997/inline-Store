#!/usr/bin/env python3
"""
Generate a professional, print-ready A4 Persian RTL Sales Invoice for Mehr Asl Manufacturing Co.
"""
import base64
from pathlib import Path

# Load authentic Mehr Asl logo as base64 data URI
logo_path = Path("/home/user/inline-Store/MehrAsl_Store_Preview/assets/logo-mehrasl.png")
if not logo_path.exists():
    raise FileNotFoundError(f"Logo not found at {logo_path}")

logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("ascii")
logo_data_uri = f"data:image/png;base64,{logo_b64}"

html_content = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>فاکتور فروش رسمی — شرکت کارخانجات تولیدی مهراصل</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    /* --- CSS Reset & Variables --- */
    *, *::before, *::after {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    :root {{
      --brand-dark-green: #14532d;
      --brand-green: #1B5E20;
      --brand-green-light: #2e7d32;
      --brand-green-subtle: #e8f5e9;
      --brand-green-bg: #f0fdf4;
      --brand-green-border: #a7f3d0;
      
      --gray-900: #0f172a;
      --gray-800: #1e293b;
      --gray-700: #334155;
      --gray-600: #475569;
      --gray-500: #64748b;
      --gray-400: #94a3b8;
      --gray-300: #cbd5e1;
      --gray-200: #e2e8f0;
      --gray-100: #f1f5f9;
      --gray-50: #f8fafc;
      
      --gold-accent: #b45309;
      --blue-accent: #1d4ed8;
      --danger: #b91c1c;

      --font-family: 'Vazirmatn', -apple-system, BlinkMacSystemFont, 'Segoe UI', Tahoma, Arial, sans-serif;
    }}

    body {{
      font-family: var(--font-family);
      background-color: #0b1320;
      color: var(--gray-800);
      line-height: 1.45;
      font-size: 11.5px;
      direction: rtl;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      padding: 24px 12px 60px;
    }}

    /* --- Interactive Top Toolbar (Screen Only) --- */
    .screen-toolbar {{
      max-width: 210mm;
      margin: 0 auto 16px;
      background: #1e293b;
      color: #f8fafc;
      padding: 12px 20px;
      border-radius: 12px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      box-shadow: 0 10px 25px -5px rgba(0,0,0,0.4);
      border: 1px solid rgba(255,255,255,0.1);
    }}

    .toolbar-left, .toolbar-right {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }}

    .toolbar-title {{
      font-weight: 700;
      font-size: 13px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .toolbar-title span.badge {{
      background: var(--brand-green);
      color: #fff;
      padding: 2px 8px;
      border-radius: 6px;
      font-size: 11px;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 14px;
      font-size: 12px;
      font-weight: 600;
      border-radius: 8px;
      cursor: pointer;
      border: none;
      transition: all 0.15s ease-in-out;
      font-family: inherit;
    }}

    .btn-primary {{
      background: #16a34a;
      color: #ffffff;
      box-shadow: 0 2px 6px rgba(22, 163, 74, 0.4);
    }}

    .btn-primary:hover {{
      background: #15803d;
    }}

    .btn-secondary {{
      background: #334155;
      color: #f1f5f9;
      border: 1px solid #475569;
    }}

    .btn-secondary:hover {{
      background: #475569;
    }}

    .status-group {{
      display: flex;
      background: #0f172a;
      padding: 3px;
      border-radius: 8px;
      gap: 2px;
      border: 1px solid #334155;
    }}

    .status-btn {{
      padding: 5px 10px;
      font-size: 11px;
      font-family: inherit;
      border: none;
      background: transparent;
      color: #94a3b8;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s;
    }}

    .status-btn.active {{
      background: var(--brand-green);
      color: #ffffff;
      font-weight: 700;
    }}

    /* --- A4 Page Container --- */
    .invoice-wrapper {{
      max-width: 210mm;
      min-height: 297mm;
      margin: 0 auto;
      background: #ffffff;
      padding: 10mm 12mm 10mm;
      box-shadow: 0 15px 35px rgba(0, 0, 0, 0.35);
      border-radius: 4px;
      position: relative;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}

    /* Decorative Top Bar */
    .top-accent-bar {{
      height: 4px;
      background: linear-gradient(90deg, var(--brand-dark-green) 0%, var(--brand-green) 50%, #4ade80 100%);
      border-radius: 2px;
      margin-bottom: 12px;
    }}

    /* --- Invoice Header --- */
    .invoice-header {{
      display: grid;
      grid-template-columns: 180px 1fr 200px;
      align-items: center;
      gap: 16px;
      padding-bottom: 12px;
      border-bottom: 2px solid var(--brand-green);
      position: relative;
    }}

    .header-logo-col {{
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      justify-content: center;
    }}

    .header-logo {{
      max-width: 175px;
      max-height: 62px;
      object-fit: contain;
      filter: drop-shadow(0 1px 2px rgba(0,0,0,0.08));
    }}

    .logo-subtitle {{
      font-size: 9px;
      font-weight: 700;
      color: var(--brand-dark-green);
      margin-top: 4px;
      letter-spacing: -0.2px;
    }}

    .header-title-col {{
      text-align: center;
    }}

    .official-badge {{
      display: inline-block;
      font-size: 9.5px;
      font-weight: 600;
      color: var(--brand-dark-green);
      background: var(--brand-green-subtle);
      border: 1px solid var(--brand-green-border);
      padding: 1px 10px;
      border-radius: 12px;
      margin-bottom: 4px;
    }}

    .invoice-title {{
      font-size: 20px;
      font-weight: 900;
      color: var(--brand-dark-green);
      line-height: 1.2;
      letter-spacing: -0.5px;
    }}

    .invoice-subtitle {{
      font-size: 10px;
      color: var(--gray-600);
      margin-top: 3px;
      font-weight: 500;
    }}

    .header-meta-col {{
      background: var(--gray-50);
      border: 1px solid var(--gray-200);
      border-radius: 8px;
      padding: 8px 10px;
      font-size: 10.5px;
    }}

    .meta-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 2px 0;
      border-bottom: 1px dashed var(--gray-200);
    }}

    .meta-row:last-child {{
      border-bottom: none;
    }}

    .meta-label {{
      color: var(--gray-500);
      font-size: 10px;
    }}

    .meta-value {{
      font-weight: 700;
      color: var(--gray-900);
      font-feature-settings: "tnum";
    }}

    .meta-value.highlight {{
      color: var(--brand-green);
      font-size: 11px;
    }}

    .invoice-status-tag {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      border-radius: 6px;
      font-weight: 700;
      font-size: 10.5px;
    }}

    .status-paid {{
      background: #dcfce7;
      color: #15803d;
      border: 1px solid #86efac;
    }}

    .status-pending {{
      background: #fef3c7;
      color: #b45309;
      border: 1px solid #fde68a;
    }}

    .status-proforma {{
      background: #dbeafe;
      color: #1d4ed8;
      border: 1px solid #bfdbfe;
    }}

    /* --- Participant Cards: Seller & Buyer Grid --- */
    .party-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 10px;
    }}

    .party-card {{
      border: 1px solid var(--gray-300);
      border-radius: 6px;
      overflow: hidden;
      background: #ffffff;
    }}

    .party-card.seller-card {{
      border-top: 3px solid var(--brand-green);
    }}

    .party-card.buyer-card {{
      border-top: 3px solid var(--brand-green-light);
    }}

    .party-card-header {{
      background: var(--gray-50);
      padding: 5px 10px;
      font-weight: 800;
      font-size: 11px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--gray-200);
    }}

    .party-card-header .title-text {{
      display: flex;
      align-items: center;
      gap: 6px;
      color: var(--brand-dark-green);
    }}

    .party-badge {{
      font-size: 9px;
      font-weight: 700;
      padding: 1px 6px;
      border-radius: 4px;
      background: var(--gray-200);
      color: var(--gray-700);
    }}

    .party-card-body {{
      padding: 8px 10px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 5px 12px;
      font-size: 10px;
    }}

    .party-field {{
      display: flex;
      flex-direction: row;
      align-items: baseline;
      gap: 4px;
    }}

    .party-field.full-span {{
      grid-column: span 2;
    }}

    .field-key {{
      color: var(--gray-500);
      white-space: nowrap;
      font-size: 9.5px;
    }}

    .field-val {{
      font-weight: 600;
      color: var(--gray-900);
      font-feature-settings: "tnum";
    }}

    .field-val.company-name {{
      font-size: 11px;
      font-weight: 800;
      color: var(--brand-dark-green);
    }}

    /* --- Products Table --- */
    .table-section {{
      margin-top: 10px;
    }}

    .section-headline {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 4px;
    }}

    .section-title {{
      font-size: 11px;
      font-weight: 800;
      color: var(--brand-dark-green);
      display: flex;
      align-items: center;
      gap: 5px;
    }}

    .section-title::before {{
      content: "";
      display: inline-block;
      width: 4px;
      height: 12px;
      background: var(--brand-green);
      border-radius: 2px;
    }}

    .table-note {{
      font-size: 9.5px;
      color: var(--gray-500);
    }}

    .items-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 10px;
      border: 1px solid var(--gray-300);
      border-radius: 6px;
      overflow: hidden;
    }}

    .items-table thead th {{
      background: var(--brand-dark-green);
      color: #ffffff;
      padding: 6px 4px;
      font-weight: 700;
      font-size: 9.5px;
      text-align: center;
      border: 1px solid rgba(255, 255, 255, 0.15);
      white-space: nowrap;
    }}

    .items-table thead th.text-right {{
      text-align: right;
      padding-right: 8px;
    }}

    .items-table tbody tr {{
      border-bottom: 1px solid var(--gray-200);
      transition: background-color 0.1s;
    }}

    .items-table tbody tr:hover {{
      background-color: var(--brand-green-bg);
    }}

    .items-table td {{
      padding: 6px 4px;
      text-align: center;
      vertical-align: middle;
      border: 1px solid var(--gray-200);
      font-feature-settings: "tnum";
    }}

    .items-table td.text-right {{
      text-align: right;
      padding-right: 8px;
    }}

    .items-table td.text-left {{
      text-align: left;
      padding-left: 8px;
      font-weight: 600;
    }}

    .item-desc-cell {{
      text-align: right !important;
      padding: 6px 8px !important;
    }}

    .item-title {{
      font-weight: 800;
      color: var(--gray-900);
      font-size: 11px;
      margin-bottom: 2px;
    }}

    .item-subtitle {{
      font-size: 9px;
      color: var(--gray-600);
      line-height: 1.3;
    }}

    .product-thumb-wrap {{
      width: 44px;
      height: 44px;
      background: var(--gray-50);
      border: 1px solid var(--gray-200);
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto;
      overflow: hidden;
      box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
    }}

    .sku-code {{
      font-family: inherit;
      font-weight: 700;
      color: var(--brand-dark-green);
      background: var(--brand-green-subtle);
      padding: 2px 5px;
      border-radius: 4px;
      display: inline-block;
      font-size: 9.5px;
      letter-spacing: 0.5px;
      direction: ltr;
    }}

    .brand-pill {{
      font-weight: 700;
      font-size: 9.5px;
      color: var(--gray-800);
      direction: ltr;
      display: inline-block;
    }}

    .model-code {{
      font-weight: 700;
      color: var(--gray-700);
      font-size: 9.5px;
      direction: ltr;
      display: inline-block;
    }}

    .qty-number {{
      font-weight: 800;
      font-size: 11px;
    }}

    .price-cell {{
      font-weight: 600;
      color: var(--gray-800);
    }}

    .discount-cell {{
      color: var(--danger);
      font-weight: 600;
    }}

    .tax-cell {{
      color: var(--gray-700);
    }}

    .line-total-cell {{
      font-weight: 800;
      color: var(--brand-dark-green);
      font-size: 11px;
    }}

    /* --- Compact Product Extra Specs Bar --- */
    .product-tech-bar {{
      margin-top: 4px;
      background: var(--gray-50);
      border: 1px dashed var(--gray-300);
      border-radius: 6px;
      padding: 5px 10px;
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 6px;
      font-size: 9.5px;
    }}

    .tech-item {{
      display: flex;
      align-items: center;
      gap: 4px;
    }}

    .tech-item .tech-key {{
      color: var(--gray-500);
      white-space: nowrap;
    }}

    .tech-item .tech-val {{
      font-weight: 700;
      color: var(--gray-800);
    }}

    /* --- Middle Split: Financial Breakdown & Logistics --- */
    .middle-section {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 10px;
    }}

    .info-card {{
      border: 1px solid var(--gray-300);
      border-radius: 6px;
      overflow: hidden;
      background: #ffffff;
      display: flex;
      flex-direction: column;
    }}

    .info-card-header {{
      background: var(--gray-100);
      padding: 5px 10px;
      font-weight: 700;
      font-size: 10.5px;
      color: var(--gray-800);
      border-bottom: 1px solid var(--gray-200);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}

    .info-card-body {{
      padding: 7px 10px;
      font-size: 10px;
      flex: 1;
    }}

    /* Financial Summary Card */
    .finance-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 10px;
    }}

    .finance-table tr {{
      border-bottom: 1px solid var(--gray-200);
    }}

    .finance-table tr:last-child {{
      border-bottom: none;
    }}

    .finance-table td {{
      padding: 4px 0;
      font-feature-settings: "tnum";
    }}

    .finance-table td.val {{
      text-align: left;
      font-weight: 700;
      color: var(--gray-800);
    }}

    .finance-table tr.total-row {{
      background: var(--brand-dark-green);
      color: #ffffff;
    }}

    .finance-table tr.total-row td {{
      padding: 7px 8px;
      font-weight: 800;
      font-size: 12px;
      color: #ffffff;
    }}

    .finance-table tr.total-row td.val {{
      color: #ffffff;
      font-size: 13.5px;
    }}

    .amount-words-box {{
      background: var(--brand-green-subtle);
      border: 1px solid var(--brand-green-border);
      border-radius: 6px;
      padding: 5px 8px;
      margin-top: 6px;
      font-size: 10px;
    }}

    .amount-words-title {{
      font-weight: 700;
      color: var(--brand-dark-green);
      font-size: 9.5px;
      margin-bottom: 1px;
    }}

    .amount-words-text {{
      font-weight: 800;
      color: var(--brand-dark-green);
      font-size: 10.5px;
    }}

    /* Payment & Shipping Combined Card */
    .delivery-payment-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 6px;
      font-size: 9.5px;
    }}

    .sub-section-title {{
      font-weight: 700;
      color: var(--brand-dark-green);
      font-size: 10px;
      border-bottom: 1px solid var(--gray-200);
      padding-bottom: 2px;
      margin-bottom: 3px;
      display: flex;
      align-items: center;
      gap: 4px;
    }}

    .detail-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 3px 8px;
    }}

    .detail-item {{
      display: flex;
      gap: 4px;
      align-items: baseline;
    }}

    .detail-item.full {{
      grid-column: span 2;
    }}

    .detail-item .lbl {{
      color: var(--gray-500);
      white-space: nowrap;
    }}

    .detail-item .val {{
      font-weight: 600;
      color: var(--gray-900);
      font-feature-settings: "tnum";
    }}

    /* --- Terms & Conditions Section --- */
    .terms-section {{
      margin-top: 8px;
      border: 1px solid var(--gray-300);
      border-radius: 6px;
      background: var(--gray-50);
      padding: 6px 10px;
    }}

    .terms-header {{
      font-size: 10px;
      font-weight: 800;
      color: var(--brand-dark-green);
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 4px;
    }}

    .terms-list {{
      list-style-type: none;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 3px 12px;
      font-size: 9px;
      color: var(--gray-700);
      line-height: 1.35;
    }}

    .terms-list li {{
      position: relative;
      padding-right: 12px;
    }}

    .terms-list li::before {{
      content: "▪";
      position: absolute;
      right: 0;
      color: var(--brand-green);
      font-size: 11px;
      line-height: 1;
    }}

    /* --- Official Signatures Section --- */
    .signatures-section {{
      margin-top: 10px;
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
    }}

    .signature-box {{
      border: 1px dashed var(--gray-400);
      border-radius: 6px;
      background: #ffffff;
      padding: 6px 8px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      height: 78px;
      text-align: center;
      position: relative;
    }}

    .sig-title {{
      font-size: 10px;
      font-weight: 700;
      color: var(--gray-800);
      border-bottom: 1px solid var(--gray-200);
      padding-bottom: 3px;
    }}

    .sig-subtitle {{
      font-size: 8.5px;
      color: var(--gray-500);
      margin-top: 1px;
    }}

    .sig-placeholder {{
      font-size: 9px;
      color: var(--gray-400);
      display: flex;
      align-items: center;
      justify-content: center;
      flex: 1;
      font-style: italic;
    }}

    /* Digital Seal graphic inside Seller Stamp Box */
    .digital-seal {{
      position: absolute;
      left: 12px;
      bottom: 6px;
      width: 60px;
      height: 60px;
      opacity: 0.85;
      pointer-events: none;
    }}

    /* --- Document Footer --- */
    .invoice-footer {{
      margin-top: 12px;
      padding-top: 8px;
      border-top: 1px solid var(--gray-300);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      font-size: 9px;
      color: var(--gray-600);
    }}

    .footer-left {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .footer-qr-wrap {{
      width: 44px;
      height: 44px;
      background: #ffffff;
      border: 1px solid var(--gray-300);
      padding: 2px;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    .footer-contacts {{
      line-height: 1.45;
    }}

    .footer-contacts b {{
      color: var(--brand-dark-green);
    }}

    .footer-right {{
      text-align: left;
      line-height: 1.45;
      direction: ltr;
    }}

    .tax-uuid {{
      font-family: monospace;
      font-weight: 700;
      color: var(--gray-700);
      font-size: 8.5px;
    }}

    .page-number {{
      font-size: 9px;
      color: var(--gray-500);
      direction: rtl;
      font-weight: 600;
    }}

    /* --- Print Styles (A4 Exact) --- */
    @page {{
      size: A4 portrait;
      margin: 8mm 10mm 8mm 10mm;
    }}

    @media print {{
      body {{
        background: #ffffff !important;
        padding: 0 !important;
        color: #000000 !important;
        font-size: 10.5px !important;
      }}

      .screen-toolbar {{
        display: none !important;
      }}

      .invoice-wrapper {{
        max-width: 100% !important;
        min-height: auto !important;
        padding: 0 !important;
        margin: 0 !important;
        box-shadow: none !important;
        border-radius: 0 !important;
        page-break-after: avoid;
        page-break-inside: avoid;
      }}

      /* Force exact color print fidelity */
      *, *::before, *::after {{
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }}

      .items-table thead th {{
        background-color: #14532d !important;
        color: #ffffff !important;
      }}

      .finance-table tr.total-row {{
        background-color: #14532d !important;
        color: #ffffff !important;
      }}

      .status-paid {{
        background-color: #dcfce7 !important;
        color: #15803d !important;
      }}
    }}
  </style>
</head>
<body>

  <!-- Screen-Only Interactive Action Bar -->
  <div class="screen-toolbar">
    <div class="toolbar-left">
      <div class="toolbar-title">
        <span>سامانه صدور فاکتور مهراصل</span>
        <span class="badge">A4 رسمی RTL</span>
      </div>
      <div class="status-group" role="group" aria-label="تغییر وضعیت فاکتور">
        <button type="button" class="status-btn active" onclick="setStatus('paid')">پرداخت شده</button>
        <button type="button" class="status-btn" onclick="setStatus('pending')">در انتظار پرداخت</button>
        <button type="button" class="status-btn" onclick="setStatus('proforma')">پیش‌فاکتور</button>
      </div>
    </div>
    <div class="toolbar-right">
      <button type="button" class="btn btn-secondary" onclick="toggleCurrency()" id="currToggleBtn">
        <span>نمایش به تومان</span>
      </button>
      <button type="button" class="btn btn-primary" onclick="window.print()">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"></polyline><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path><rect x="6" y="14" width="12" height="8"></rect></svg>
        <span>چاپ سند / ذخیره PDF</span>
      </button>
    </div>
  </div>

  <!-- A4 Printable Invoice Document -->
  <main class="invoice-wrapper" id="invoiceDocument">
    
    <div>
      <!-- Top Decorative Green Stripe -->
      <div class="top-accent-bar"></div>

      <!-- 1. Header Section -->
      <header class="invoice-header">
        <!-- Logo Column -->
        <div class="header-logo-col">
          <img class="header-logo" src="{logo_data_uri}" alt="لوگوی رسمی شرکت کارخانجات تولیدی مهراصل">
          <div class="logo-subtitle">شرکت کارخانجات تولیدی مهراصل</div>
        </div>

        <!-- Center Title Column -->
        <div class="header-title-col">
          <div class="official-badge">صورتحساب الکترونیکی سامانه جامع امور مالیاتی</div>
          <h1 class="invoice-title" id="invoiceMainHeading">فاکتور فروش کالا و خدمات</h1>
          <div class="invoice-subtitle" id="invoiceSubHeading">فاکتور قطعی و سند فروش رسمی — شماره اختصاصی مؤدیان</div>
        </div>

        <!-- Metadata Column -->
        <div class="header-meta-col">
          <div class="meta-row">
            <span class="meta-label">شماره فاکتور:</span>
            <span class="meta-value highlight" id="docNumber">INV-1405-89421</span>
          </div>
          <div class="meta-row">
            <span class="meta-label">شماره سفارش:</span>
            <span class="meta-value">ORD-2026-98104</span>
          </div>
          <div class="meta-row">
            <span class="meta-label">تاریخ صدور:</span>
            <span class="meta-value">۱۴۰۵/۰۶/۲۶</span>
          </div>
          <div class="meta-row">
            <span class="meta-label">ساعت صدور:</span>
            <span class="meta-value">۱۰:۴۲:۱۵</span>
          </div>
          <div class="meta-row">
            <span class="meta-label">وضعیت سند:</span>
            <span class="invoice-status-tag status-paid" id="statusBadge">
              ● پرداخت شده
            </span>
          </div>
        </div>
      </header>

      <!-- 2. Seller and Buyer Cards Grid -->
      <section class="party-grid" aria-label="اطلاعات فروشنده و خریدار">
        <!-- Seller Card (فروشنده: مهراصل) -->
        <article class="party-card seller-card">
          <div class="party-card-header">
            <div class="title-text">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M3 21h18M3 7v14M21 7v14M6 11h4M6 15h4M14 11h4M14 15h4M9 3l3-2 3 2v4H9z"/></svg>
              <span>مشخصات فروشنده (صادرکننده)</span>
            </div>
            <span class="party-badge">حقوقی / تولیدکننده</span>
          </div>
          <div class="party-card-body">
            <div class="party-field full-span">
              <span class="field-key">نام شرکت:</span>
              <span class="field-val company-name">شرکت کارخانجات تولیدی مهراصل (سهامی خاص)</span>
            </div>
            <div class="party-field">
              <span class="field-key">نام تجاری:</span>
              <span class="field-val">مهراصل (Mehr Asl)</span>
            </div>
            <div class="party-field">
              <span class="field-key">شماره ثبت:</span>
              <span class="field-val">۷۰۰۸۱</span>
            </div>
            <div class="party-field">
              <span class="field-key">شناسه ملی:</span>
              <span class="field-val">۱۰۱۰۱۱۴۰۰۰۱</span>
            </div>
            <div class="party-field">
              <span class="field-key">کد اقتصادی:</span>
              <span class="field-val">۴۱۱۱۳۸۸۴۱۱۱۱</span>
            </div>
            <div class="party-field">
              <span class="field-key">استان / شهر:</span>
              <span class="field-val">تهران / تهران (دفتر مرکزی)</span>
            </div>
            <div class="party-field">
              <span class="field-key">کد پستی:</span>
              <span class="field-val">۱۵۷۵۷۳۳۵۱۱</span>
            </div>
            <div class="party-field">
              <span class="field-key">تلفن فروش:</span>
              <span class="field-val">۰۲۱-۸۸۳۰۰۸۰۱</span>
            </div>
            <div class="party-field">
              <span class="field-key">تلفن کارخانه:</span>
              <span class="field-val">۰۴۱-۳۴۳۲۸۹۴۱</span>
            </div>
            <div class="party-field full-span">
              <span class="field-key">نشانی دفتر مرکزی:</span>
              <span class="field-val">تهران، خیابان مفتح شمالی، خیابان زهره، شماره ۱۷، ساختمان مهراصل</span>
            </div>
            <div class="party-field">
              <span class="field-key">ایمیل سازمانی:</span>
              <span class="field-val">sales.manager@mehrasl.ir</span>
            </div>
            <div class="party-field">
              <span class="field-key">پایگاه اینترنتی:</span>
              <span class="field-val">www.mehrasl.ir</span>
            </div>
          </div>
        </article>

        <!-- Buyer Card (خریدار) -->
        <article class="party-card buyer-card">
          <div class="party-card-header">
            <div class="title-text">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
              <span>مشخصات خریدار (مشتری)</span>
            </div>
            <span class="party-badge">شخص حقوقی</span>
          </div>
          <div class="party-card-body">
            <div class="party-field full-span">
              <span class="field-key">نام شخص / شرکت:</span>
              <span class="field-val company-name">شرکت مهندسی و توسعه صنایع نوین اروند</span>
            </div>
            <div class="party-field">
              <span class="field-key">نوع مشتری:</span>
              <span class="field-val">حقوقی (صنعتی)</span>
            </div>
            <div class="party-field">
              <span class="field-key">شماره ثبت:</span>
              <span class="field-val">۵۴۱۲۹۰</span>
            </div>
            <div class="party-field">
              <span class="field-key">شناسه ملی:</span>
              <span class="field-val">۱۴۰۰۸۲۹۱۰۳۴</span>
            </div>
            <div class="party-field">
              <span class="field-key">کد اقتصادی:</span>
              <span class="field-val">۴۱۱۶۸۴۳۲۵۹۱۷</span>
            </div>
            <div class="party-field">
              <span class="field-key">استان / شهر:</span>
              <span class="field-val">تهران / تهران</span>
            </div>
            <div class="party-field">
              <span class="field-key">کد پستی:</span>
              <span class="field-val">۱۹۸۵۷۱۴۳۲۹</span>
            </div>
            <div class="party-field">
              <span class="field-key">تلفن ثابت:</span>
              <span class="field-val">۰۲۱-۲۲۶۵۴۳۲۱</span>
            </div>
            <div class="party-field">
              <span class="field-key">تلفن همراه:</span>
              <span class="field-val">۰۹۱۲۳۴۵۶۷۸۹</span>
            </div>
            <div class="party-field full-span">
              <span class="field-key">نشانی کامل:</span>
              <span class="field-val">تهران، بزرگراه شهید چمران، خیابان ملاصدرا، پلاک ۸۴، طبقه ۴، واحد ۱۲</span>
            </div>
            <div class="party-field">
              <span class="field-key">نماینده تحویل:</span>
              <span class="field-val">مهندس کامران صبوری</span>
            </div>
            <div class="party-field">
              <span class="field-key">پست الکترونیک:</span>
              <span class="field-val">procurement@arvand-ind.ir</span>
            </div>
          </div>
        </article>
      </section>

      <!-- 3. Products Table Section -->
      <section class="table-section" aria-label="جدول اقلام فاکتور">
        <div class="section-headline">
          <div class="section-title">مشخصات کالا یا خدمات مورد معامله</div>
          <div class="table-note">واحد ارزی مبنا: <b id="currencyName">ریال جمهوری اسلامی ایران</b></div>
        </div>

        <table class="items-table">
          <thead>
            <tr>
              <th style="width: 28px;">ردیف</th>
              <th style="width: 48px;">تصویر</th>
              <th class="text-right">شرح کالا / مشخصات فنی و استاندارد</th>
              <th style="width: 72px;">برند</th>
              <th style="width: 72px;">مدل</th>
              <th style="width: 85px;">کد کالا (SKU)</th>
              <th style="width: 38px;">تعداد</th>
              <th style="width: 40px;">واحد</th>
              <th style="width: 82px;">قیمت واحد</th>
              <th style="width: 68px;">مبلغ تخفیف</th>
              <th style="width: 68px;">مالیات (%۱۰)</th>
              <th style="width: 95px;">مبلغ کل نهایی</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><b>۱</b></td>
              <td>
                <div class="product-thumb-wrap" title="کنتاکتور FORENANCE 41NB30AL">
                  <!-- Detailed Technical SVG Contactor Illustration -->
                  <svg width="36" height="36" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="15" y="10" width="70" height="80" rx="8" fill="#2d3748" stroke="#1a202c" stroke-width="3"/>
                    <rect x="22" y="16" width="56" height="68" rx="4" fill="#3b475a"/>
                    <!-- Terminal Blocks Top -->
                    <rect x="22" y="8" width="14" height="12" rx="2" fill="#718096" stroke="#1a202c" stroke-width="1.5"/>
                    <rect x="43" y="8" width="14" height="12" rx="2" fill="#718096" stroke="#1a202c" stroke-width="1.5"/>
                    <rect x="64" y="8" width="14" height="12" rx="2" fill="#718096" stroke="#1a202c" stroke-width="1.5"/>
                    <circle cx="29" cy="14" r="3" fill="#e2e8f0"/>
                    <circle cx="50" cy="14" r="3" fill="#e2e8f0"/>
                    <circle cx="71" cy="14" r="3" fill="#e2e8f0"/>
                    <!-- Main Window & Forenance Badge -->
                    <rect x="28" y="28" width="44" height="32" rx="3" fill="#1B5E20" stroke="#14532d" stroke-width="1.5"/>
                    <rect x="33" y="32" width="34" height="12" rx="2" fill="#ffffff"/>
                    <text x="50" y="41" font-family="Arial, sans-serif" font-size="7.5" font-weight="900" fill="#14532d" text-anchor="middle">FORENANCE</text>
                    <text x="50" y="54" font-family="Arial, sans-serif" font-size="6.5" font-weight="bold" fill="#ffffff" text-anchor="middle">41NB30AL</text>
                    <!-- Status indicator -->
                    <rect x="38" y="66" width="24" height="6" rx="1.5" fill="#e53e3e"/>
                    <circle cx="43" cy="69" r="1.5" fill="#ffffff"/>
                    <!-- Terminal Blocks Bottom -->
                    <rect x="22" y="80" width="14" height="12" rx="2" fill="#718096" stroke="#1a202c" stroke-width="1.5"/>
                    <rect x="43" y="80" width="14" height="12" rx="2" fill="#718096" stroke="#1a202c" stroke-width="1.5"/>
                    <rect x="64" y="80" width="14" height="12" rx="2" fill="#718096" stroke="#1a202c" stroke-width="1.5"/>
                    <circle cx="29" cy="86" r="3" fill="#e2e8f0"/>
                    <circle cx="50" cy="86" r="3" fill="#e2e8f0"/>
                    <circle cx="71" cy="86" r="3" fill="#e2e8f0"/>
                  </svg>
                </div>
              </td>
              <td class="item-desc-cell">
                <div class="item-title">کنتاکتور FORENANCE 41NB30AL</div>
                <div class="item-subtitle">کنتاکتور قدرت صنعتی سه پل، بوبین 220V AC 50/60Hz، با کنتاکت کمکی 1NO+1NC، سازگار با رله حرارتی بی‌متال و نصب روی ریل DIN ۳۵ میلی‌متری تابلو برق</div>
              </td>
              <td><span class="brand-pill">FORENANCE</span></td>
              <td><span class="model-code">41NB30AL</span></td>
              <td><span class="sku-code">1010001000002</span></td>
              <td><span class="qty-number">۱</span></td>
              <td>عدد</td>
              <td class="price-cell"><span data-irr="54000000">۵۴,۰۰۰,۰۰۰</span></td>
              <td class="discount-cell"><span data-irr="2700000">۲,۷۰۰,۰۰۰</span></td>
              <td class="tax-cell"><span data-irr="5130000">۵,۱۳۰,۰۰۰</span></td>
              <td class="line-total-cell"><span data-irr="56430000">۵۶,۴۳۰,۰۰۰</span></td>
            </tr>
          </tbody>
        </table>

        <!-- 4. Additional Product Technical Specs Bar (Compact) -->
        <div class="product-tech-bar">
          <div class="tech-item">
            <span class="tech-key">شماره سریال:</span>
            <span class="tech-val" style="direction: ltr;">SN-FRN-41NB-2026-09028</span>
          </div>
          <div class="tech-item">
            <span class="tech-key">کشور سازنده / مبدأ:</span>
            <span class="tech-val">فرانسه (تحت لیسانس FORENANCE)</span>
          </div>
          <div class="tech-item">
            <span class="tech-key">دوره گارانتی:</span>
            <span class="tech-val">۱۸ ماه ضمانت طلایی مهراصل</span>
          </div>
          <div class="tech-item">
            <span class="tech-key">خدمات پس از فروش:</span>
            <span class="tech-val">۱۰ سال پشتیبانی فنی قطعات</span>
          </div>
        </div>
      </section>

      <!-- 5. Middle Split: Financial Summary & Payment/Shipping Details -->
      <section class="middle-section">
        
        <!-- Left: Financial Summary -->
        <article class="info-card">
          <div class="info-card-header">
            <div style="display:flex; align-items:center; gap:5px;">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
              <span>خلاصه محاسبات مالی صورتحساب</span>
            </div>
            <span style="font-size: 9.5px; color: var(--gray-500);">مبالغ به <span class="curr-unit-label">ریال</span></span>
          </div>
          <div class="info-card-body">
            <table class="finance-table">
              <tr>
                <td>مجموع مبلغ ناخالص (پایه):</td>
                <td class="val"><span data-irr="54000000">۵۴,۰۰۰,۰۰۰</span> <span class="curr-unit-label">ریال</span></td>
              </tr>
              <tr>
                <td>مجموع تخفیف ویژه مشتریان حقوقی (۵٪):</td>
                <td class="val" style="color: var(--danger);">(<span data-irr="2700000">۲,۷۰۰,۰۰۰</span>) <span class="curr-unit-label">ریال</span></td>
              </tr>
              <tr>
                <td>خالص کل پس از تخفیف:</td>
                <td class="val"><span data-irr="51300000">۵۱,۳۰۰,۰۰۰</span> <span class="curr-unit-label">ریال</span></td>
              </tr>
              <tr>
                <td>مالیات و عوارض بر ارزش افزوده (۱۰٪):</td>
                <td class="val"><span data-irr="5130000">۵,۱۳۰,۰۰۰</span> <span class="curr-unit-label">ریال</span></td>
              </tr>
              <tr>
                <td>هزینه بسته‌بندی ایمن و ارسال صنعتی:</td>
                <td class="val"><span data-irr="1500000">۱,۵۰۰,۰۰۰</span> <span class="curr-unit-label">ریال</span></td>
              </tr>
              <tr>
                <td>سایر عوارض و خدمات فنی:</td>
                <td class="val">۰ <span class="curr-unit-label">ریال</span></td>
              </tr>
              <tr class="total-row">
                <td>مبلغ کل قابل پرداخت:</td>
                <td class="val"><span data-irr="57930000" id="finalTotalSpan">۵۷,۹۳۰,۰۰۰</span> <span class="curr-unit-label">ریال</span></td>
              </tr>
            </table>

            <div class="amount-words-box">
              <div class="amount-words-title">مبلغ قابل پرداخت به حروف:</div>
              <div class="amount-words-text" id="amountInWords">
                پنجاه و هفت میلیون و نهصد و سی هزار ریال تمام
              </div>
            </div>
          </div>
        </article>

        <!-- Right: Payment & Delivery Information -->
        <article class="info-card">
          <div class="info-card-header">
            <div style="display:flex; align-items:center; gap:5px;">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect><line x1="1" y1="10" x2="23" y2="10"></line></svg>
              <span>اطلاعات پرداخت و ارسال سفارش</span>
            </div>
            <span style="font-size: 9.5px; color: var(--brand-dark-green); font-weight: 700;">تسویه سازمانی</span>
          </div>
          <div class="info-card-body delivery-payment-grid">
            
            <!-- Payment sub-block -->
            <div>
              <div class="sub-section-title">
                <span>مشخصات تسویه و تراکنش بانکی</span>
              </div>
              <div class="detail-grid">
                <div class="detail-item">
                  <span class="lbl">روش پرداخت:</span>
                  <span class="val">حواله پایا / ساتنا بانکی</span>
                </div>
                <div class="detail-item">
                  <span class="lbl">وضعیت پرداخت:</span>
                  <span class="val" style="color: #15803d; font-weight: 800;">پرداخت قطعی (تایید مالی)</span>
                </div>
                <div class="detail-item">
                  <span class="lbl">کد پیگیری تراکنش:</span>
                  <span class="val" style="direction: ltr;">TRX-948120673411</span>
                </div>
                <div class="detail-item">
                  <span class="lbl">تاریخ و زمان پرداخت:</span>
                  <span class="val">۱۴۰۵/۰۶/۲۶ - ۱۰:۴۸:۲۲</span>
                </div>
                <div class="detail-item full">
                  <span class="lbl">شماره شبا مقصد:</span>
                  <span class="val" style="direction: ltr; font-size: 9px;">IR68 0120 0000 0000 1234 5678 90</span>
                  <span style="color: var(--gray-500); font-size: 8.5px;">(بانک ملت — مهراصل)</span>
                </div>
              </div>
            </div>

            <!-- Shipping sub-block -->
            <div style="margin-top: 4px;">
              <div class="sub-section-title">
                <span>مشخصات باربری و ارسال محموله</span>
              </div>
              <div class="detail-grid">
                <div class="detail-item">
                  <span class="lbl">روش تحویل:</span>
                  <span class="val">باربری اختصاصی / تیپاکس اکسپرس</span>
                </div>
                <div class="detail-item">
                  <span class="lbl">شماره بارنامه:</span>
                  <span class="val" style="direction: ltr;">BAR-88291044</span>
                </div>
                <div class="detail-item">
                  <span class="lbl">تحویل‌گیرنده:</span>
                  <span class="val">مهندس کامران صبوری</span>
                </div>
                <div class="detail-item">
                  <span class="lbl">موعد تخمینی تحویل:</span>
                  <span class="val">۱۴۰۵/۰۶/۲۸ (۴۸ ساعت کاری)</span>
                </div>
                <div class="detail-item full">
                  <span class="lbl">نشانی مقصد:</span>
                  <span class="val">تهران، خ ملاصدرا، پلاک ۸۴، طبقه ۴، واحد ۱۲</span>
                </div>
              </div>
            </div>

          </div>
        </article>

      </section>

      <!-- 6. Sale Terms & Warranty Notes -->
      <section class="terms-section" aria-label="توضیحات و شرایط فروش">
        <div class="terms-header">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
          <span>توضیحات، شرایط فروش و ضوابط خدمات پس از فروش شرکت کارخانجات تولیدی مهراصل:</span>
        </div>
        <ul class="terms-list">
          <li><b>شرایط پرداخت و تسویه:</b> این سند پس از دریافت تاییدیه مالیه شرکت مهراصل و تسویه قطعی اعتبار قانونی دارد.</li>
          <li><b>مهلت انصراف و مرجوعی:</b> استرداد کالا حداکثر تا ۷ روز تقویمی پس از تحویل، منوط به سلامت کامل جعبه و پلمپ فابریک شرکت امکان‌پذیر است.</li>
          <li><b>ضوابط گارانتی ۱۸ ماهه:</b> هرگونه اتصال غیراستاندارد، تغییر سیم‌بندی فابریک بوبین، و نوسانات خارج از رنج ولتاژ موجب خروج از گارانتی می‌گردد.</li>
          <li><b>تحویل فیزیکی محموله:</b> خریدار موظف است حین تحویل بار سلامت فیزیکی کارتن را بررسی نموده و قبض تحویل بارنامه را پس از تایید امضا نماید.</li>
        </ul>
      </section>

      <!-- 7. Official Signatures & Stamp Boxes -->
      <section class="signatures-section" aria-label="محل مهر و امضا">
        <!-- Box 1: Seller -->
        <div class="signature-box">
          <div class="sig-title">مهر و امضای فروشنده (صادرکننده)</div>
          <div class="sig-subtitle">امور مالی و فروش شرکت تولیدی مهراصل</div>
          <div class="sig-placeholder">
            <!-- Official Mehr Asl Stamp Graphic Placeholder -->
            <svg class="digital-seal" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
              <circle cx="60" cy="60" r="54" fill="none" stroke="#1B5E20" stroke-width="2.5" stroke-dasharray="4 2"/>
              <circle cx="60" cy="60" r="48" fill="none" stroke="#1B5E20" stroke-width="1.2"/>
              <path id="curve" fill="none" d="M 22,60 A 38,38 0 1,1 98,60 A 38,38 0 1,1 22,60" />
              <text font-family="'Vazirmatn', Arial" font-size="8" font-weight="bold" fill="#1B5E20">
                <textPath href="#curve" startOffset="50%" text-anchor="middle">
                  شرکت کارخانجات تولیدی مهراصل ★ واحد مالی
                </textPath>
              </text>
              <text x="60" y="58" font-family="'Vazirmatn', Arial" font-size="10" font-weight="900" fill="#1B5E20" text-anchor="middle">تایید شد</text>
              <text x="60" y="70" font-family="'Vazirmatn', Arial" font-size="7.5" fill="#14532d" text-anchor="middle">۱۴۰۵/۰۶/۲۶</text>
            </svg>
            <span>مهر دیجیتال ثبت سامانه جامع مهراصل</span>
          </div>
        </div>

        <!-- Box 2: Warehouse Dispatcher -->
        <div class="signature-box">
          <div class="sig-title">مهر و امضای انباردار / تحویل‌دهنده</div>
          <div class="sig-subtitle">واحد انبار مرکزی و کنترل کیفیت مهراصل</div>
          <div class="sig-placeholder">
            <span>امضا و مهر خروج از انبار سلیمی</span>
          </div>
        </div>

        <!-- Box 3: Buyer -->
        <div class="signature-box">
          <div class="sig-title">مهر و امضای خریدار / تحویل‌گیرنده</div>
          <div class="sig-subtitle">شرکت مهندسی و توسعه صنایع نوین اروند</div>
          <div class="sig-placeholder">
            <span>صحت اقلام و سلامت بسته دریافت شد</span>
          </div>
        </div>
      </section>
    </div>

    <!-- 8. Document Footer -->
    <footer class="invoice-footer">
      <div class="footer-left">
        <div class="footer-qr-wrap" title="کد اصالت الکترونیکی صورتحساب">
          <!-- Vector QR Code representation -->
          <svg width="40" height="40" viewBox="0 0 33 33" fill="#14532d">
            <rect x="0" y="0" width="9" height="9" fill="#14532d"/>
            <rect x="2" y="2" width="5" height="5" fill="#ffffff"/>
            <rect x="3.5" y="3.5" width="2" height="2" fill="#14532d"/>
            
            <rect x="24" y="0" width="9" height="9" fill="#14532d"/>
            <rect x="26" y="2" width="5" height="5" fill="#ffffff"/>
            <rect x="27.5" y="3.5" width="2" height="2" fill="#14532d"/>
            
            <rect x="0" y="24" width="9" height="9" fill="#14532d"/>
            <rect x="2" y="26" width="5" height="5" fill="#ffffff"/>
            <rect x="3.5" y="27.5" width="2" height="2" fill="#14532d"/>
            
            <rect x="12" y="2" width="3" height="3"/>
            <rect x="18" y="4" width="3" height="2"/>
            <rect x="12" y="10" width="4" height="4"/>
            <rect x="18" y="12" width="4" height="2"/>
            <rect x="14" y="18" width="5" height="4"/>
            <rect x="22" y="18" width="3" height="3"/>
            <rect x="12" y="26" width="4" height="4"/>
            <rect x="24" y="24" width="3" height="6"/>
            <rect x="28" y="28" width="3" height="3"/>
          </svg>
        </div>
        <div class="footer-contacts">
          <div><b>پشتیبانی مشتریان مهراصل:</b> ۰۲۱-۸۸۳۰۰۸۰۱ | <b>فکس:</b> ۰۲۱-۸۸۳۰۳۸۱۲ | <b>خط مستقیم کارخانه تبریز:</b> ۰۴۱-۳۴۳۲۸۹۴۱</div>
          <div><b>ایمیل سازمانی:</b> sales.manager@mehrasl.ir | <b>وب‌سایت رسمی:</b> <a href="https://www.mehrasl.ir" target="_blank" style="color:var(--brand-dark-green); text-decoration:none; font-weight:700;">www.mehrasl.ir</a></div>
        </div>
      </div>
      <div class="footer-right">
        <div class="tax-uuid">UUID: A09B-1405-E84C-99B1-MEHR</div>
        <div class="page-number">صفحه ۱ از ۱</div>
      </div>
    </footer>

  </main>

  <!-- Interactive Logic for Status Toggling & Currency Conversion -->
  <script>
    let currentCurrency = 'irr'; // 'irr' or 'toman'
    const wordForms = {{
      irr: 'پنجاه و هفت میلیون و نهصد و سی هزار ریال تمام',
      toman: 'پنج میلیون و هفتصد و نود و سه هزار تومان تمام'
    }};

    function setStatus(status) {{
      const badge = document.getElementById('statusBadge');
      const docNum = document.getElementById('docNumber');
      const mainHead = document.getElementById('invoiceMainHeading');
      const subHead = document.getElementById('invoiceSubHeading');
      
      // Update buttons
      document.querySelectorAll('.status-btn').forEach(btn => btn.classList.remove('active'));
      
      if (status === 'paid') {{
        event.target.classList.add('active');
        badge.className = 'invoice-status-tag status-paid';
        badge.innerHTML = '● پرداخت شده';
        docNum.textContent = 'INV-1405-89421';
        mainHead.textContent = 'فاکتور فروش کالا و خدمات';
        subHead.textContent = 'فاکتور قطعی و سند فروش رسمی — شماره اختصاصی مؤدیان';
      }} else if (status === 'pending') {{
        event.target.classList.add('active');
        badge.className = 'invoice-status-tag status-pending';
        badge.innerHTML = '● در انتظار پرداخت';
        docNum.textContent = 'INV-1405-89421';
        mainHead.textContent = 'فاکتور فروش کالا و خدمات';
        subHead.textContent = 'صورتحساب فروش — موعد تسویه: ۲۴ ساعت کاری';
      }} else if (status === 'proforma') {{
        event.target.classList.add('active');
        badge.className = 'invoice-status-tag status-proforma';
        badge.innerHTML = '● پیش‌فاکتور رسمی';
        docNum.textContent = 'PRO-1405-89421';
        mainHead.textContent = 'پیش‌فاکتور رسمی (استعلام بها)';
        subHead.textContent = 'پیش‌فاکتور معتبر جهت اخذ مجوز خرید و تأمین اعتبار — اعتبار: ۳ روز کاری';
      }}
    }}

    function toggleCurrency() {{
      const btn = document.getElementById('currToggleBtn');
      const currName = document.getElementById('currencyName');
      const wordsEl = document.getElementById('amountInWords');
      const labels = document.querySelectorAll('.curr-unit-label');
      const spans = document.querySelectorAll('[data-irr]');

      if (currentCurrency === 'irr') {{
        currentCurrency = 'toman';
        btn.querySelector('span').textContent = 'نمایش به ریال (رسمی)';
        currName.textContent = 'تومان ایران (معادل ریالی)';
        wordsEl.textContent = wordForms.toman;
        labels.forEach(l => l.textContent = 'تومان');
        
        spans.forEach(el => {{
          const irr = parseInt(el.getAttribute('data-irr'), 10);
          const toman = Math.floor(irr / 10);
          el.textContent = toman.toLocaleString('fa-IR');
        }});
      }} else {{
        currentCurrency = 'irr';
        btn.querySelector('span').textContent = 'نمایش به تومان';
        currName.textContent = 'ریال جمهوری اسلامی ایران';
        wordsEl.textContent = wordForms.irr;
        labels.forEach(l => l.textContent = 'ریال');
        
        spans.forEach(el => {{
          const irr = parseInt(el.getAttribute('data-irr'), 10);
          el.textContent = irr.toLocaleString('fa-IR');
        }});
      }}
    }}
  </script>
</body>
</html>
"""

# Write to root directory and preview directory
root_path = Path("/home/user/inline-Store/invoice-mehrasl.html")
root_path.write_text(html_content, encoding="utf-8")
print(f"Generated root invoice: {root_path} ({root_path.stat().st_size:,} bytes)")

preview_path = Path("/home/user/inline-Store/MehrAsl_Store_Preview/invoice.html")
preview_path.write_text(html_content, encoding="utf-8")
print(f"Generated preview invoice: {preview_path} ({preview_path.stat().st_size:,} bytes)")
