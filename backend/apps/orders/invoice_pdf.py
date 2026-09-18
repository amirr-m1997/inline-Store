"""Render the official invoice HTML to an A4 PDF with headless Chromium.

Why Chromium instead of reportlab: the official invoice is a full CSS design
(gradient header, styled tables, badges). Re-implementing it with reportlab
primitives produced the "simple" invoice nobody wants. Chromium prints the
exact same document the customer previews, including backgrounds.

The bundled Vazirmatn subsets (apps/orders/fonts/) are embedded as base64
@font-face rules so the PDF is deterministic even on servers without Persian
system fonts or internet access to Google Fonts.
"""
from __future__ import annotations

import base64
import os
import shutil
import subprocess
import tempfile

FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")
_FONT_FILES = (
    ("Vazirmatn-Arabic-400.woff2", 400),
    ("Vazirmatn-Arabic-700.woff2", 700),
    ("Vazirmatn-Latin-400.woff2", 400),
    ("Vazirmatn-Latin-700.woff2", 700),
)


class InvoicePdfError(Exception):
    """Raised when the invoice PDF cannot be produced."""


def _font_face_css() -> str:
    rules = []
    for filename, weight in _FONT_FILES:
        path = os.path.join(FONTS_DIR, filename)
        if not os.path.exists(path):
            continue
        with open(path, "rb") as handle:
            encoded = base64.b64encode(handle.read()).decode("ascii")
        rules.append(
            "@font-face{font-family:'Vazirmatn';font-style:normal;font-weight:%d;"
            "font-display:swap;src:url(data:font/woff2;base64,%s) format('woff2');}"
            % (weight, encoded)
        )
    return "".join(rules)


def find_chromium() -> str:
    from django.conf import settings

    explicit = getattr(settings, "INVOICE_CHROMIUM_PATH", "") or os.environ.get("INVOICE_CHROMIUM_PATH", "")
    if explicit and os.path.exists(explicit):
        return explicit
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    if os.name == "nt":
        for candidate in (
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ):
            if os.path.exists(candidate):
                return candidate
    return ""


def render_invoice_pdf_bytes(html: str, timeout: int = 120) -> bytes:
    """Print invoice HTML to A4 PDF bytes. Raises InvoicePdfError on failure."""
    binary = find_chromium()
    if not binary:
        raise InvoicePdfError(
            "Chromium executable not found. Install Chromium or set INVOICE_CHROMIUM_PATH."
        )
    document = html.replace("</head>", "<style>%s</style></head>" % _font_face_css(), 1)
    with tempfile.TemporaryDirectory(prefix="invoice-pdf-") as tmp:
        source = os.path.join(tmp, "invoice.html")
        output = os.path.join(tmp, "invoice.pdf")
        with open(source, "w", encoding="utf-8") as handle:
            handle.write(document)
        try:
            completed = subprocess.run(
                [binary, "--headless=new", "--no-sandbox", "--disable-gpu",
                 "--no-pdf-header-footer", "--virtual-time-budget=10000",
                 f"--print-to-pdf={output}", f"file://{source}"],
                capture_output=True, timeout=timeout, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise InvoicePdfError(f"Chromium PDF render failed: {exc}") from exc
        if completed.returncode != 0 or not os.path.exists(output):
            raise InvoicePdfError(
                "Chromium PDF render failed: %s" % (completed.stderr.decode("utf-8", "replace")[-500:] or f"exit {completed.returncode}")
            )
        with open(output, "rb") as handle:
            return handle.read()
