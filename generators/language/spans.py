"""T08: occurrence-aware span extraction.

A small, reusable utility (usable by T09 later) implementing guidelines.md
Section 13.2's rule: "The span validator resolves occurrences by walking all
matches in order and selecting index n. It must never use a bare
str.find(), which always returns the first match and silently mislabels
every repeat."

find_occurrence() walks *every* match explicitly rather than trusting a
single str.find() call to be correct -- it fails closed
(SpanResolutionError) if the requested occurrence_index does not correspond
to an actual match, rather than guessing or silently returning something
else.
"""

from __future__ import annotations


class SpanResolutionError(ValueError):
    """Raised when the intended PII occurrence cannot be uniquely resolved."""


def find_all_occurrences(text: str, value: str) -> list:
    """Walk every occurrence of `value` in `text`, in order. Never a bare
    str.find() -- this is the explicit occurrence-walking loop guidelines.md
    Section 13.2 requires."""
    if not value:
        raise SpanResolutionError("cannot locate an empty value")
    matches = []
    search_start = 0
    while True:
        idx = text.find(value, search_start)
        if idx == -1:
            break
        matches.append(idx)
        search_start = idx + 1  # advance by 1, not len(value): tolerates overlaps
    return matches


def find_occurrence(text: str, value: str, occurrence_index: int = 0):
    """Return (start, end) for the occurrence_index-th occurrence of `value`
    in `text` (Unicode code-point offsets -- Python str slicing). Fails
    closed if the occurrence cannot be uniquely resolved."""
    matches = find_all_occurrences(text, value)
    if occurrence_index >= len(matches):
        raise SpanResolutionError(
            f"occurrence_index={occurrence_index} requested but only "
            f"{len(matches)} occurrence(s) of {value!r} found in text"
        )
    start = matches[occurrence_index]
    end = start + len(value)
    if text[start:end] != value:
        raise SpanResolutionError(
            f"span contract violated: text[{start}:{end}] != {value!r}"
        )
    return start, end
