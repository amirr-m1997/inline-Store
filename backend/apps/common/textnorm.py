"""Persian display normalization (Arabic keyboard variants -> Persian forms).

Keyboards in the field are Arabic, so database text is full of Arabic code
points (ي U+064A, ك U+0643, ...). They must never reach the browser as-is:
every outgoing display surface is normalized to Persian forms.

Deliberately NOT mapped: ؤ (U+0624), ئ (U+0626), أ (U+0623) and إ (U+0625).
They are correct Persian orthography (مؤسسه، جزئیات، رئیس، تأیید، تأمین)
— an Arabic keyboard produces the very same code points, so mapping them
would corrupt correct text ("جزئیات" -> "جزییات", "تأمین" -> "تامین").
Verified against production data: every أ in the catalog is the word
تأمین. Latin digits are left untouched (SKUs, order numbers, phone numbers
stay LTR).
"""

_ARABIC_TO_PERSIAN = str.maketrans(
    {
        "\u064a": "\u06cc",  # ARABIC LETTER YEH -> FARSI YEH (ی)
        "\u0649": "\u06cc",  # ARABIC LETTER ALEF MAKSURA -> FARSI YEH (ی)
        "\u0643": "\u06a9",  # ARABIC LETTER KAF -> KEHEH (ک)
        "\u0629": "\u0647",  # ARABIC LETTER TEH MARBUTA -> HEH (ه)
        "\u0660": "\u06f0",
        "\u0661": "\u06f1",
        "\u0662": "\u06f2",
        "\u0663": "\u06f3",
        "\u0664": "\u06f4",
        "\u0665": "\u06f5",
        "\u0666": "\u06f6",
        "\u0667": "\u06f7",
        "\u0668": "\u06f8",
        "\u0669": "\u06f9",  # ARABIC-INDIC DIGITS -> EXTENDED (PERSIAN) DIGITS
    }
)


def normalize_persian_text(value):
    """Map Arabic keyboard variants to Persian forms (non-strings pass through)."""
    if not isinstance(value, str) or not value:
        return value
    return value.translate(_ARABIC_TO_PERSIAN)


def normalize_json_data(value):
    """Recursively normalize every string inside a JSON-like structure."""
    if isinstance(value, str):
        return normalize_persian_text(value)
    if isinstance(value, dict):
        return {key: normalize_json_data(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize_json_data(item) for item in value]
    return value
