from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from .service import DownloadWorker, YTDLPLogger


class BatchSourceWorker(QObject):
    """Download account feeds or collections with yt-dlp in a Qt worker thread."""

    progress = Signal(int)
    status = Signal(str)
    log = Signal(str)
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        text: str,
        source_kind: str,
        platform: str,
        output_directory: str,
        max_items: int = 20,
        tiktok_cookie: str = "",
        douyin_cookie: str = "",
        tiktok_proxy: str = "",
        douyin_proxy: str = "",
    ) -> None:
        super().__init__()
        self.text = text.strip()
        self.source_kind = source_kind.strip().lower()
        self.platform = platform.strip().lower()
        self.output_directory = output_directory
        self.max_items = max(1, int(max_items))
        self.tiktok_cookie = tiktok_cookie.strip()
        self.douyin_cookie = douyin_cookie.strip()
        self.tiktok_proxy = tiktok_proxy.strip()
        self.douyin_proxy = douyin_proxy.strip()
        self._source_index = 0
        self._source_total = 1
        self._current_title = ""

    @Slot()
    def run(self) -> None:
        try:
            result = self._download()
        except Exception as exc:
            self.failed.emit(self._friendly_error(exc))
            return
        self.finished.emit(result)

    def _download(self) -> dict[str, Any]:
        urls = DownloadWorker.extract_urls(self.text)
        if not urls:
            label = "account/profile" if self.source_kind == "account" else "collection/playlist"
            raise ValueError(f"Paste at least one complete {label} link.")

        output = Path(self.output_directory).expanduser().resolve()
        output.mkdir(parents=True, exist_ok=True)
        self._source_total = len(urls)

        self.log.emit(
            "Mode: "
            + ("Account feed download" if self.source_kind == "account" else "Collection download")
        )
        self.log.emit(f"Maximum items per link: {self.max_items}")
        self.log.emit(f"Save folder: {output}")
        self.progress.emit(0)

        results: list[dict[str, str]] = []
        for index, url in enumerate(urls, start=1):
            self._source_index = index
            platform = DownloadWorker.detect_platform(url, self.platform)
            self.status.emit(f"Processing source {index} of {len(urls)}…")
            self.log.emit(f"[{index}/{len(urls)}] {url}")

            info = self._download_source(url, platform, output)
            entries = self._flatten_entries(info)
            if not entries and info.get("id"):
                entries = [info]

            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                results.append(
                    {
                        "id": str(entry.get("id") or ""),
                        "title": str(entry.get("title") or entry.get("id") or "Downloaded item"),
                        "platform": platform,
                        "url": str(entry.get("webpage_url") or url),
                        "filename": DownloadWorker._resolve_filename(entry),
                    }
                )

            if not entries:
                self.log.emit("No downloadable entries were returned for this link.")
            else:
                self.log.emit(f"Completed source: {len(entries)} item(s)")
            self.progress.emit(int(index / len(urls) * 100))

        if not results:
            raise RuntimeError(
                "No media was downloaded. The profile or collection may be private, empty, "
                "region-restricted, or require a fresh cookie."
            )

        self.progress.emit(100)
        self.status.emit(f"Completed · {len(results)} item(s)")
        return {
            "kind": self.source_kind,
            "count": len(results),
            "output_directory": str(output),
            "results": results,
        }

    def _download_source(
        self, url: str, platform: str, output: Path
    ) -> dict[str, Any]:
        cookie = self.tiktok_cookie if platform == "tiktok" else self.douyin_cookie
        proxy = self.tiktok_proxy if platform == "tiktok" else self.douyin_proxy

        if self.source_kind == "account":
            template = (
                "%(uploader|Unknown)s/"
                "%(upload_date>%Y-%m-%d)s - %(title).120B [%(id)s].%(ext)s"
            )
        else:
            template = (
                "%(playlist_title|Collection)s/"
                "%(playlist_index)03d - %(title).120B [%(id)s].%(ext)s"
            )

        options: dict[str, Any] = {
            "format": "best[ext=mp4]/best",
            "paths": {"home": str(output)},
            "outtmpl": template,
            "windowsfilenames": True,
            "noplaylist": False,
            "playlistend": self.max_items,
            "continuedl": True,
            "overwrites": False,
            "ignoreerrors": True,
            "quiet": True,
            "no_warnings": True,
            "logger": YTDLPLogger(self.log),
            "progress_hooks": [self._progress_hook],
            "retries": 5,
            "fragment_retries": 5,
            "socket_timeout": 20,
        }
        if cookie:
            options["http_headers"] = {"Cookie": cookie}
        if proxy:
            options["proxy"] = proxy

        with YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=True)
            if not isinstance(info, dict):
                raise RuntimeError("The downloader did not return account or collection data.")
            return info

    def _progress_hook(self, data: dict[str, Any]) -> None:
        status = str(data.get("status") or "")
        info = data.get("info_dict") or {}
        title = str(info.get("title") or info.get("id") or "media")
        if title != self._current_title:
            self._current_title = title
            self.log.emit(f"Downloading: {title}")

        if status == "downloading":
            downloaded = int(data.get("downloaded_bytes") or 0)
            total = int(data.get("total_bytes") or data.get("total_bytes_estimate") or 0)
            item_percent = int(downloaded * 100 / total) if total else 0
            item_percent = max(0, min(item_percent, 99))
            source_progress = (
                (self._source_index - 1) + (item_percent / 100)
            ) / self._source_total
            self.progress.emit(max(1, min(int(source_progress * 100), 99)))

            speed = DownloadWorker._human_speed(data.get("speed"))
            eta = data.get("eta")
            detail = title
            if speed:
                detail += f" · {speed}"
            if eta is not None:
                detail += f" · {int(eta)}s left"
            self.status.emit(detail)
        elif status == "finished":
            filename = Path(str(data.get("filename") or "")).name
            if filename:
                self.log.emit(f"Saved media: {filename}")

    @classmethod
    def _flatten_entries(cls, info: dict[str, Any]) -> list[dict[str, Any]]:
        entries = info.get("entries")
        if not entries:
            return []
        flattened: list[dict[str, Any]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            nested = cls._flatten_entries(entry)
            if nested:
                flattened.extend(nested)
            elif entry.get("id"):
                flattened.append(entry)
        return flattened

    @staticmethod
    def _friendly_error(exc: Exception) -> str:
        message = str(exc).strip() or type(exc).__name__
        if isinstance(exc, DownloadError):
            message = re.sub(r"^ERROR:\s*", "", message)
            return (
                "yt-dlp could not process this source:\n"
                f"{message}\n\n"
                "Try a public profile/collection link first. If the page requires login, "
                "open Settings and paste a fresh Cookie from your own browser session."
            )
        return f"{type(exc).__name__}: {message}"
