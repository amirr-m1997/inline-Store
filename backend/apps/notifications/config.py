from django.core.exceptions import ImproperlyConfigured


def parse_env_bool(value, *, default=False):
    """Parse an environment boolean without treating every non-empty value as true."""
    if value is None or value == "":
        return default
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise ImproperlyConfigured(f"Invalid boolean environment value: {value!r}")
