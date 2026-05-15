from __future__ import annotations

import json
import logging
import re
import threading
from dataclasses import dataclass
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .project_links import GITHUB_REPO

log = logging.getLogger(__name__)

GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
USER_AGENT = "Subnautica2-Mod-Manager-Updater"
IGNORED_ASSET_SUFFIXES = (".sha256", ".sha1", ".txt", ".sig", ".asc", ".json")
PREFERRED_ASSET_SUFFIXES = (".zip", ".7z", ".msi", ".exe")


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    download_url: str
    size: int = 0


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    html_url: str
    assets: list[ReleaseAsset]

    @property
    def preferred_asset(self) -> ReleaseAsset | None:
        return pick_preferred_asset(self.assets)

    @property
    def display_version(self) -> str:
        return self.version if self.version.startswith("v") else f"v{self.version}"


@dataclass(frozen=True)
class UpdateCheckResult:
    status: str
    message: str
    release: ReleaseInfo | None = None

    @property
    def update_available(self) -> bool:
        return self.status == "available"


def check_for_update(
    current_version: str,
    callback: Callable[[ReleaseInfo], None],
    no_update_callback: Callable[[], None] | None = None,
    error_callback: Callable[[str], None] | None = None,
) -> None:
    def _worker() -> None:
        result = check_for_update_sync(current_version)
        if result.update_available and result.release is not None:
            callback(result.release)
        elif result.status == "current":
            if no_update_callback:
                no_update_callback()
        elif error_callback:
            error_callback(result.message)

    threading.Thread(target=_worker, daemon=True).start()


def check_for_update_sync(current_version: str) -> UpdateCheckResult:
    try:
        release = fetch_latest_release()
    except Exception as exc:
        return UpdateCheckResult("error", friendly_error(exc))
    if is_newer_version(release.version, current_version):
        return UpdateCheckResult(
            "available",
            f"Update available: {release.display_version}",
            release,
        )
    return UpdateCheckResult("current", f"Already up to date: {current_version}", release)


def fetch_latest_release() -> ReleaseInfo:
    request = Request(
        GITHUB_API_URL,
        headers={"Accept": "application/vnd.github.v3+json", "User-Agent": USER_AGENT},
    )
    with urlopen(request, timeout=8) as response:
        data = json.loads(response.read().decode("utf-8"))
    return release_info_from_api(data)


def release_info_from_api(data: dict) -> ReleaseInfo:
    assets = [
        ReleaseAsset(
            name=str(asset.get("name") or ""),
            download_url=str(asset.get("browser_download_url") or ""),
            size=int(asset.get("size") or 0),
        )
        for asset in data.get("assets", [])
        if asset.get("name") and asset.get("browser_download_url")
    ]
    return ReleaseInfo(
        version=str(data.get("tag_name") or data.get("name") or "").strip().lstrip("vV"),
        html_url=str(data.get("html_url") or ""),
        assets=assets,
    )


def pick_preferred_asset(assets: list[ReleaseAsset]) -> ReleaseAsset | None:
    candidates = [
        asset
        for asset in assets
        if asset.name and not asset.name.casefold().endswith(IGNORED_ASSET_SUFFIXES)
    ]
    if not candidates:
        return None
    for suffix in PREFERRED_ASSET_SUFFIXES:
        for asset in candidates:
            if asset.name.casefold().endswith(suffix):
                return asset
    return candidates[0]


def is_newer_version(remote: str, local: str) -> bool:
    remote_parts = version_parts(remote)
    local_parts = version_parts(local)
    if not remote_parts or not local_parts:
        return False
    max_len = max(len(remote_parts), len(local_parts))
    remote_parts.extend([0] * (max_len - len(remote_parts)))
    local_parts.extend([0] * (max_len - len(local_parts)))
    return remote_parts > local_parts


def version_parts(version: str) -> list[int]:
    raw = str(version or "").strip().lstrip("vV")
    if not raw:
        return []
    matches = re.findall(r"\d+", raw)
    return [int(value) for value in matches[:4]]


def friendly_error(exc: Exception) -> str:
    if isinstance(exc, HTTPError):
        if exc.code == 404:
            return "No GitHub release has been published yet."
        return f"GitHub returned HTTP {exc.code}."
    if isinstance(exc, URLError):
        return f"Could not reach GitHub: {exc.reason}"
    return str(exc)
