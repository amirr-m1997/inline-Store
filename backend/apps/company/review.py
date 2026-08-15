"""Pure, read-only review classification for company-content approval."""


def _text(value):
    return str(value or "").strip()


def _relation_count(obj, name):
    relation = getattr(obj, name, None)
    return relation.count() if relation is not None else 0


def review_record(kind, obj):
    title = _text(getattr(obj, "name_fa", "") or getattr(obj, "title_fa", ""))
    english = _text(getattr(obj, "name_en", "") or getattr(obj, "title_en", ""))
    source_url = _text(getattr(obj, "source_url", ""))
    source_title = _text(getattr(obj, "source_title", ""))
    missing = []
    verification_needed = False

    if kind == "CompanyLocation":
        if not _text(getattr(obj, "address_fa", "")): missing.append("Persian address")
        if getattr(obj, "verification_required", True): verification_needed = True
        if not _text(getattr(obj, "working_hours", "")): missing.append("working hours")
    elif kind == "CompanyMilestone":
        if not _text(getattr(obj, "date_label", "")): missing.append("date/year")
        if not _text(getattr(obj, "description_fa", "")): missing.append("minimal factual description")
        verification_needed = True
    elif kind == "CompanyCertification":
        for field, label in (("certificate_code", "standard/code"), ("issuer", "issuer"), ("file", "supporting file")):
            if not _text(getattr(obj, field, "")): missing.append(label)
        verification_needed = getattr(obj, "verification_status", "unverified") != "verified"
    elif kind == "CompanyHonor":
        for field, label in (("issuer", "issuer"), ("year_label", "year")):
            if not _text(getattr(obj, field, "")): missing.append(label)
        verification_needed = getattr(obj, "verification_required", True)
    elif kind == "Industry":
        if not _text(getattr(obj, "description_fa", "")): missing.append("Persian landing-page description")
        if _relation_count(obj, "categories") + _relation_count(obj, "products") + _relation_count(obj, "capabilities") == 0: missing.append("approved relationships")
    elif kind == "CompanySection":
        if not _text(getattr(obj, "title_fa", "")): missing.append("Persian title")
        if not (_text(getattr(obj, "summary_fa", "")) or _text(getattr(obj, "body_fa", ""))): missing.append("Persian content")
    elif kind == "Capability":
        if not _text(getattr(obj, "summary_fa", "")): missing.append("Persian summary")
        if not _text(getattr(obj, "body_fa", "")): missing.append("Persian body")
        if _relation_count(obj, "categories") + _relation_count(obj, "products") == 0: missing.append("approved catalog relationships")

    if not source_url: missing.append("source URL")
    if not english: missing.append("English translation")

    editorial_required = any(item in missing for item in ("Persian content", "Persian summary", "Persian body", "Persian landing-page description", "approved relationships", "approved catalog relationships"))
    translation_required = "English translation" in missing
    if not title and not source_url:
        classification, action = "E", "Keep archived/unpublished until authoritative content is supplied."
        decision = "ARCHIVE"
    elif verification_needed:
        classification, action = "B", "Verify facts and evidence before considering publication."
        decision = "VERIFY"
    elif editorial_required:
        classification, action = "C", "Complete a concise factual editorial rewrite before publication."
        decision = "EDIT"
    elif "English translation" in missing:
        classification, action = "D", "Obtain an approved English translation; do not machine-publish it."
        decision = "EDIT"
    else:
        classification, action = "A", "Safe to publish only after basic business confirmation."
        decision = "APPROVE"

    if getattr(obj, "is_published", False):
        status = "Published"
    elif verification_needed:
        status = "Needs verification"
    elif editorial_required or translation_required:
        status = "Needs editorial work"
    else:
        status = "Ready for business approval"

    persian_parts = [_text(getattr(obj, field, "")) for field in ("title_fa", "name_fa", "summary_fa", "description_fa", "body_fa", "address_fa")]
    english_parts = [_text(getattr(obj, field, "")) for field in ("title_en", "name_en", "summary_en", "description_en", "body_en", "address_en")]
    details = {}
    if kind == "CompanyLocation":
        details = {
            "location_type": _text(getattr(obj, "location_type", "")),
            "address": _text(getattr(obj, "address_fa", "") or getattr(obj, "address_en", "")),
            "phone": _text(getattr(obj, "phone", "")),
            "mobile": _text(getattr(obj, "mobile", "")),
            "email": _text(getattr(obj, "email", "")),
            "working_hours": _text(getattr(obj, "working_hours", "")),
        }
    elif kind == "CompanyCertification":
        details = {
            "certificate_code": _text(getattr(obj, "certificate_code", "")),
            "issuer": _text(getattr(obj, "issuer", "")),
            "scope": _text(getattr(obj, "scope", "")) or "not captured in current model",
            "issued_date": _text(getattr(obj, "issued_date", "")),
            "expiry_date": _text(getattr(obj, "expiry_date", "")),
            "supporting_file": _text(getattr(obj, "file", "")),
        }
    elif kind == "Industry":
        details = {
            "categories": _relation_count(obj, "categories"),
            "products": _relation_count(obj, "products"),
            "capabilities": _relation_count(obj, "capabilities"),
        }
    elif kind == "Capability":
        details = {
            "categories": _relation_count(obj, "categories"),
            "products": _relation_count(obj, "products"),
            "persian_summary": _text(getattr(obj, "summary_fa", "")),
            "persian_body": _text(getattr(obj, "body_fa", "")),
        }
    return {
        "kind": kind,
        "id": obj.pk,
        "title": title,
        "english_title": english,
        "source_url": source_url,
        "source_title": source_title,
        "persian": " | ".join(dict.fromkeys(part for part in persian_parts if part)),
        "english": " | ".join(dict.fromkeys(part for part in english_parts if part)),
        "verification": _text(getattr(obj, "verification_status", "required" if verification_needed else "not-required")),
        "verification_required": verification_needed,
        "translation_required": translation_required,
        "editorial_required": editorial_required,
        "status": status,
        "published": bool(getattr(obj, "is_published", False)),
        "missing": missing,
        "classification": classification,
        "recommended_decision": decision,
        "recommended_action": action,
        "details": details,
    }
