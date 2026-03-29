# Copyright Sierra
# Utilities for message content: strip <think> tags, sanitize user observations.

from typing import Optional


def strip_think_tags(content: str) -> str:
    """
    Remove <think>...</think> blocks from text (one or nested).
    Uses depth counting so inner tags are matched correctly; removes orphan tags.
    """
    if not content or not isinstance(content, str):
        return content
    out_parts: list[str] = []
    i = 0
    n = len(content)
    while i < n:
        if content[i : i + 7] == "<think>":
            depth = 1
            i += 7
            while i < n and depth > 0:
                if content[i : i + 7] == "<think>":
                    depth += 1
                    i += 7
                elif content[i : i + 8] == "</think>":
                    depth -= 1
                    if depth > 0:
                        i += 8
                    else:
                        i += 8
                        break
                else:
                    i += 1
            continue
        if content[i : i + 8] == "</think>":
            # Orphan close tag; skip it
            i += 8
            continue
        # Emit character and advance
        out_parts.append(content[i])
        i += 1
    return "".join(out_parts)


def sanitize_user_observation(content: str) -> str:
    """
    Sanitize content from user simulator before appending as role=user:
    strip <think> blocks and trim whitespace.
    """
    if not content or not isinstance(content, str):
        return content
    out = strip_think_tags(content)
    return out.strip()
