# -*- coding: utf-8 -*-
"""PEP 263-compatible source transformer for explicit emoji scopes.

Use as a preprocessing module or register it as a custom codec at interpreter
startup. It converts 🍇 / 🍉 scope markers into normal Python indentation.
"""

from __future__ import annotations

import codecs

OPEN_SCOPE = "🍇"
CLOSE_SCOPE = "🍉"
INDENT = "    "


def translate_source_text(source: str) -> str:
    """Translate explicit emoji scope markers to valid, indented Python source."""
    output: list[str] = []
    level = 0

    for raw_line in source.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            output.append("")
            continue

        closes = 0
        while stripped.startswith(CLOSE_SCOPE):
            closes += 1
            stripped = stripped[len(CLOSE_SCOPE):].lstrip()
        level = max(0, level - closes)

        opens = stripped.endswith(OPEN_SCOPE)
        if opens:
            stripped = stripped[:-len(OPEN_SCOPE)].rstrip() + ":"

        output.append(f"{INDENT * level}{stripped}")
        if opens:
            level += 1

    if level:
        raise SyntaxError(f"Unclosed emoji scope(s): {level}")
    return "\n".join(output) + "\n"


def py_emoji_decode(input_bytes: bytes, errors: str = "strict") -> tuple[str, int]:
    source = bytes(input_bytes).decode("utf-8", errors)
    return translate_source_text(source), len(input_bytes)


def py_emoji_encode(input_text: str, errors: str = "strict") -> tuple[bytes, int]:
    return input_text.encode("utf-8", errors), len(input_text)


def find_py_emoji_codec(encoding_name: str):
    normalized = encoding_name.replace("_", "-").lower()
    if normalized in {"py-emoji", "pyemoji"}:
        return codecs.CodecInfo(name="py_emoji", encode=py_emoji_encode, decode=py_emoji_decode)
    return None


codecs.register(find_py_emoji_codec)
