from __future__ import annotations

import hashlib
from pathlib import Path

_HASH_CACHE_LIMIT = 512
_HASH_CACHE: dict[tuple[str, int, int, int], str] = {}


def hash_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    stat = path.stat()
    key = (str(path.resolve()), stat.st_mtime_ns, stat.st_size, int(chunk_size))
    cached = _HASH_CACHE.get(key)
    if cached is not None:
        return cached
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    value = digest.hexdigest()
    if len(_HASH_CACHE) >= _HASH_CACHE_LIMIT:
        _HASH_CACHE.clear()
    _HASH_CACHE[key] = value
    return value


def clear_hash_cache() -> None:
    _HASH_CACHE.clear()
