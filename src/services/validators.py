"""Validation helpers."""

from __future__ import annotations


def validate_inn(inn: str) -> bool:
    """Validate that INN is 10 or 12 digits."""

    if not inn or not inn.isdigit():
        return False
    return len(inn) in {10, 12}
