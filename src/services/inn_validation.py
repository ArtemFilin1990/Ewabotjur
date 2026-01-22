"""INN validation helpers."""

from __future__ import annotations


def is_valid_inn(inn: str) -> bool:
    """Validate Russian INN length and digits only."""

    if not inn:
        return False
    if not inn.isdigit():
        return False
    return len(inn) in {10, 12}
