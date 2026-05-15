from __future__ import annotations

from pathlib import Path
from typing import Any

from ..models.app_paths import SteamAppManifest


def parse_acf_text(text: str) -> dict[str, Any]:
    """Parse Valve ACF/VDF text into nested dictionaries.

    This intentionally supports the subset Steam appmanifest/libraryfolders
    files use: quoted keys, quoted values, and nested brace objects.
    """
    tokens = _tokenize_acf(text)
    stack: list[dict[str, Any]] = [{}]
    pending_key: str | None = None

    for token in tokens:
        if token == "{":
            child: dict[str, Any] = {}
            if pending_key is None:
                continue
            stack[-1][pending_key] = child
            stack.append(child)
            pending_key = None
        elif token == "}":
            if len(stack) > 1:
                stack.pop()
            pending_key = None
        elif pending_key is None:
            pending_key = token
        else:
            stack[-1][pending_key] = token
            pending_key = None

    root = stack[0]
    if len(root) == 1 and isinstance(next(iter(root.values())), dict):
        return next(iter(root.values()))
    return root


def read_app_manifest(path: Path, *, library_root: Path | None = None) -> SteamAppManifest | None:
    try:
        data = parse_acf_text(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return None
    appid = str(data.get("appid") or "")
    if not appid:
        return None
    return SteamAppManifest(
        appid=appid,
        name=str(data.get("name") or ""),
        installdir=str(data.get("installdir") or ""),
        buildid=str(data.get("buildid") or ""),
        last_updated=str(data.get("LastUpdated") or data.get("lastupdated") or ""),
        size_on_disk=str(data.get("SizeOnDisk") or data.get("sizeondisk") or ""),
        manifest_path=path,
        library_root=library_root,
    )


def _tokenize_acf(text: str) -> list[str]:
    tokens: list[str] = []
    i = 0
    length = len(text)
    while i < length:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if ch in "{}":
            tokens.append(ch)
            i += 1
            continue
        if ch == '"':
            i += 1
            value: list[str] = []
            while i < length:
                ch = text[i]
                if ch == "\\" and i + 1 < length:
                    value.append(text[i + 1])
                    i += 2
                    continue
                if ch == '"':
                    i += 1
                    break
                value.append(ch)
                i += 1
            tokens.append("".join(value))
            continue

        start = i
        while i < length and not text[i].isspace() and text[i] not in "{}":
            i += 1
        tokens.append(text[start:i])
    return tokens
