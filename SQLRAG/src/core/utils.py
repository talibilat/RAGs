from __future__ import annotations
"""Utility helpers."""


def sanitize_sql(sql_text: str) -> str:
    """Remove Markdown fences and leading 'sql' tag if present.

    The SQL generation model sometimes returns triple-fenced code blocks.
    This helper normalises the output so it can be executed directly.
    """
    if not sql_text:
        return ""
    # Strip markdown fences and surrounding whitespace
    cleaned = sql_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        # Remove optional leading 'sql' tag
        if cleaned.lower().startswith("sql"):
            cleaned = cleaned[3:]
    return cleaned.strip()


