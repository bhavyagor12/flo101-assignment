"""Paragraph-aware recursive chunker. ~4 chars/token approximation."""

from __future__ import annotations

_CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + _CHARS_PER_TOKEN - 1) // _CHARS_PER_TOKEN)


def chunk_text(
    text: str,
    *,
    max_chars: int = 2000,
    overlap_chars: int = 200,
) -> list[str]:
    # Boundary preference, in order: blank line, newline, sentence, space.
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + max_chars, text_len)
        if end < text_len:
            # Find the latest natural break in [start + max_chars/2, end)
            window_min = start + max_chars // 2
            cut = _last_natural_break(text, window_min, end)
            if cut > start:
                end = cut
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_len:
            break
        start = max(end - overlap_chars, start + 1)
    return chunks


def _last_natural_break(text: str, lo: int, hi: int) -> int:
    for sep in ("\n\n", "\n", ". ", " "):
        idx = text.rfind(sep, lo, hi)
        if idx >= 0:
            return idx + len(sep)
    return -1
