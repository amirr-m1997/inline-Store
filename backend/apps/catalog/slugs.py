import re
import unicodedata


WORDS = {
    "آلن": "allen", "آلنی": "alleni", "اتصالات": "etesalat", "اولیه": "avalie",
    "تخت": "takht", "تولید": "tolid", "صنعتی": "sanati", "گوش": "goosh",
    "مواد": "mavade", "واشر": "washer", "های": "haye", "شش": "shesh",
    "پیچ": "pich", "و": "va",
}

LETTERS = {
    "ا": "a", "آ": "a", "أ": "a", "إ": "e", "ب": "b", "پ": "p", "ت": "t",
    "ث": "s", "ج": "j", "چ": "ch", "ح": "h", "خ": "kh", "د": "d", "ذ": "z",
    "ر": "r", "ز": "z", "ژ": "zh", "س": "s", "ش": "sh", "ص": "s", "ض": "z",
    "ط": "t", "ظ": "z", "ع": "a", "غ": "gh", "ف": "f", "ق": "gh", "ک": "k",
    "ك": "k", "گ": "g", "ل": "l", "م": "m", "ن": "n", "و": "v", "ه": "h",
    "ة": "h", "ی": "y", "ي": "y", "ئ": "y", "ء": "", "ؤ": "v",
}


def latin_category_slug(value):
    """Return a deterministic ASCII slug without depending on a category's position."""
    value = unicodedata.normalize("NFKC", value or "").replace("\u200c", " ")
    tokens = re.findall(r"[A-Za-z0-9]+|[\u0600-\u06ff]+", value)
    converted = []
    for token in tokens:
        if token in WORDS:
            converted.append(WORDS[token])
        elif token.isascii():
            converted.append(token.lower())
        else:
            converted.append("".join(LETTERS.get(char, "") for char in token))
    slug = re.sub(r"-+", "-", "-".join(filter(None, converted))).strip("-")
    return slug or "category"
