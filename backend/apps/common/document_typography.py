"""Shared typography policy for server-generated business documents.

Vazir is the required Persian document family. Deployments should provide it
through MEHRASL_VAZIR_FONT_PATH (or the standard local font locations). Until
then, generation remains operational with an explicit non-compliant fallback.
"""

import os
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class DocumentTypographyError(RuntimeError):
    pass


def _candidates(weight):
    configured = os.environ.get("MEHRASL_VAZIR_FONT_PATH", "")
    names = {"regular": "Vazir.ttf", "medium": "Vazir-Medium.ttf", "bold": "Vazir-Bold.ttf"}
    paths = [Path(configured) / names[weight]] if configured else []
    paths.extend([
        Path("/usr/share/fonts/truetype/vazir") / names[weight],
        Path("/usr/local/share/fonts") / names[weight],
        Path(__file__).resolve().parents[2] / "assets" / "fonts" / "vazir" / names[weight],
        Path(__file__).resolve().parents[2] / "static" / "fonts" / "vazir" / names[weight],
    ])
    return paths


def document_font_paths():
    vazir = {weight: next((path for path in _candidates(weight) if path.is_file()), None) for weight in ("regular", "medium", "bold")}
    latin = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    fallback = Path("/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf")
    return {"vazir": vazir, "latin": latin if latin.is_file() else None, "fallback": fallback if fallback.is_file() else latin}


def typography_status():
    paths = document_font_paths()
    return {"vazir_available": all(paths["vazir"].values()), "weights": paths["vazir"], "fallback": paths["fallback"], "latin": paths["latin"]}


def required_persian_font():
    status = typography_status()
    if not status["vazir_available"]:
        raise DocumentTypographyError("Vazir font assets are not installed. Set MEHRASL_VAZIR_FONT_PATH or install approved local Vazir weights before generating compliant Persian business documents.")
    return status["weights"]


def register_document_fonts():
    """Register the shared document font family and return stable aliases.

    Vazir is selected whenever all approved weights are available.  The
    fallback keeps legacy document generation operational in environments that
    have not installed the required asset yet; ``typography_status`` makes
    that non-compliant deployment state explicit.
    """
    paths = document_font_paths()
    persian_path = paths["vazir"]["regular"] or paths["fallback"]
    if persian_path is None:
        raise DocumentTypographyError("No usable Persian document font is available.")

    registrations = {
        "persian": ("MehraslPersian", persian_path),
        "persian_medium": ("MehraslPersianMedium", paths["vazir"]["medium"]),
        "persian_bold": ("MehraslPersianBold", paths["vazir"]["bold"]),
        "latin": ("MehraslLatin", paths["latin"]),
    }
    for name, path in registrations.values():
        if path is not None and name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(path)))
    return {
        "persian": registrations["persian"][0],
        "persian_medium": registrations["persian_medium"][0] if registrations["persian_medium"][1] else registrations["persian"][0],
        "persian_bold": registrations["persian_bold"][0] if registrations["persian_bold"][1] else registrations["persian"][0],
        "latin": registrations["latin"][0] if registrations["latin"][1] else registrations["persian"][0],
        "status": typography_status(),
    }
