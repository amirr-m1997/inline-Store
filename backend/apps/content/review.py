import hashlib
import re
import unicodedata
from collections.abc import Iterable
from datetime import datetime

from django.utils import timezone


DEMO_MARKERS = ("demo-content:", "[demo]")
IMPORT_MARKER = "mehrasl-editorial-import:"


def normalize_editorial_text(value):
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("ي", "ی").replace("ى", "ی").replace("ك", "ک")
    value = value.replace("\u200c", "")
    return re.sub(r"\s+", " ", value).strip().casefold()


def source_fingerprint(*values):
    payload = "\n".join(normalize_editorial_text(value) for value in values)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def is_demo_record(record):
    haystack = " ".join(str(getattr(record, field, "") or "") for field in ("slug", "title_fa", "question_fa", "source_url", "migration_notes"))
    lowered = haystack.casefold()
    return any(marker in lowered for marker in DEMO_MARKERS)


def is_imported_record(record):
    return IMPORT_MARKER in (getattr(record, "migration_notes", "") or "") or bool(getattr(record, "source_fingerprint", ""))


def _has_any_relation(record, names):
    return any(getattr(record, name).exists() for name in names)


def _article_flags(record):
    missing = []
    warnings = []
    if not (record.title_fa or "").strip(): missing.append("title_fa")
    if not (record.title_en or "").strip(): missing.append("title_en")
    if not (record.excerpt_fa or "").strip(): missing.append("excerpt_fa")
    if not (record.body_fa or "").strip(): missing.append("body_fa")
    if not (record.seo_title_fa or "").strip(): missing.append("seo_title_fa")
    if not (record.seo_description_fa or "").strip(): missing.append("seo_description_fa")
    if not (record.seo_title_en or "").strip(): missing.append("seo_title_en")
    if not (record.seo_description_en or "").strip(): missing.append("seo_description_en")
    if not record.featured_image: missing.append("featured_image")
    if not record.category_id: missing.append("category")
    if not _has_any_relation(record, ("products", "catalog_categories", "brands", "industries", "capabilities")):
        missing.append("relationships")
    imported = is_imported_record(record)
    if imported and not (record.source_url or "").strip(): missing.append("source_url")
    if imported and not (record.source_title or "").strip(): missing.append("source_title")
    if record.published_at and record.published_at > timezone.now(): warnings.append("future_publication")
    if record.content_type == "product_guide" and not _has_any_relation(record, ("products", "catalog_categories")):
        warnings.append("product_guide_without_product_or_category")
    if record.content_type == "buying_guide" and not _has_any_relation(record, ("products", "catalog_categories")):
        warnings.append("buying_guide_without_product_or_category")
    if record.content_type == "technical_article" and not _has_any_relation(record, ("catalog_categories", "industries", "capabilities")):
        warnings.append("technical_article_without_context")
    if record.is_published and not _has_any_relation(record, ("products", "catalog_categories", "brands", "industries", "capabilities")):
        warnings.append("published_without_relationships")
    if len((record.title_fa or "").strip()) < 12: warnings.append("title_too_short")
    if len((record.title_fa or "").strip()) > 180: warnings.append("title_too_long")
    return missing, warnings, imported


def _faq_flags(record):
    missing = []
    warnings = []
    if not (record.question_fa or "").strip(): missing.append("question_fa")
    if not (record.question_en or "").strip(): missing.append("question_en")
    if not (record.answer_fa or "").strip(): missing.append("answer_fa")
    if not (record.answer_en or "").strip(): missing.append("answer_en")
    if not _has_any_relation(record, ("products", "categories", "industries", "capabilities", "articles")):
        missing.append("relationships")
    imported = is_imported_record(record)
    if imported and not (record.source_url or "").strip(): missing.append("source_url")
    if imported and not (record.source_title or "").strip(): missing.append("source_title")
    if record.faq_type == "product" and not record.products.exists(): warnings.append("product_faq_without_product")
    if len((record.answer_fa or "").strip()) < 30: warnings.append("answer_too_short")
    return missing, warnings, imported


def duplicate_keys(record):
    return [
        ("source_url", normalize_editorial_text(getattr(record, "source_url", ""))),
        ("slug", normalize_editorial_text(getattr(record, "slug", ""))),
        ("title_fa" if hasattr(record, "title_fa") else "question_fa", normalize_editorial_text(getattr(record, "title_fa", None) or getattr(record, "question_fa", ""))),
    ]


def evaluate_record(record, duplicate_index=None):
    if record.__class__.__name__ == "ContentArticle":
        missing, warnings, imported = _article_flags(record)
    else:
        missing, warnings, imported = _faq_flags(record)
    duplicate_candidates = []
    if duplicate_index is not None:
        for key in duplicate_keys(record):
            if key[1] and len(duplicate_index.get(key, ())) > 1:
                duplicate_candidates.append(f"{key[0]}:{key[1]}")
        if duplicate_candidates:
            warnings.append("duplicate_candidate")
    return {
        "model": record.__class__.__name__,
        "id": record.pk,
        "title": getattr(record, "title_fa", None) or getattr(record, "question_fa", ""),
        "content_type": getattr(record, "content_type", None) or getattr(record, "faq_type", None),
        "review_status": getattr(record, "review_status", "draft"),
        "is_published": bool(getattr(record, "is_published", False)),
        "is_demo": is_demo_record(record),
        "is_imported": imported,
        "missing": missing,
        "warnings": warnings,
        "duplicate_candidates": duplicate_candidates,
        "recommended_action": "manual_review" if missing or warnings or getattr(record, "review_status", "draft") != "ready" else "no_action",
    }


def duplicate_groups(records: Iterable):
    buckets = {}
    for record in records:
        keys = [("title" if key == "title_fa" else key, value) for key, value in duplicate_keys(record)]
        for key, value in keys:
            if value:
                buckets.setdefault((key, value), []).append(record)
    return {key: items for key, items in buckets.items() if len(items) > 1}


def duplicate_index(records: Iterable):
    buckets = {}
    for record in records:
        for key in duplicate_keys(record):
            if key[1]:
                buckets.setdefault(key, []).append(record.pk)
    return buckets
