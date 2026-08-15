import re
import unicodedata


_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_search_text(value):
    """Canonicalize Persian/Arabic search text for identifiers and queries."""
    text = unicodedata.normalize("NFKC", value or "")
    text = text.translate(_DIGITS).replace("ي", "ی").replace("ى", "ی").replace("ك", "ک")
    text = text.replace("\u200c", "").replace("\u200f", " ").replace("\u200e", " ")
    return re.sub(r"\s+", " ", text).strip().casefold()
