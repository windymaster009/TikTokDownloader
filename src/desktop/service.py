from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)


class YTDLPLogger:
    """Forward useful yt-dlp messages to the desktop log without console spam."""

    def __init__(self, signal: Signal) -> None:
        self.signal = signal

    def debug(self, message: str) -> None:
        if message.startswith("[debug]"):
            return
        if message.startswith("[download]") and "Destination:" in message:
            self.signal.emit(message.replace("[download]", "").strip())

    def info(self, message: str) -> None:
        if message:
            self.signal.emit(message)

    def warning(self, message: str) -> None:
        if message:
            self.signal.emit(f"Warning: {message}")

    def error(self, message: str) -> None:
        if message:
            self.signal.emit(message)


class DownloadWorker(QObject):
    """Download public TikTok/Douyin links in a worker thread using yt-dlp."""

    progress = Signal(int)
    status = Signal(str)
    log = Signal(str)
    item_started = Signal(int, int, str, str)
    item_title = Signal(int, str)
    item_progress = Signal(int, int, str)
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        text: str,
        platform: str,
        output_directory: str,
        tiktok_cookie: str = "",
        douyin_cookie: str = "",
        tiktok_proxy: str = "",
        douyin_proxy: str = "",
    ) -> None:
        super().__init__()
        self.text = text.strip()
        self.platform = platform
        self.output_directory = output_directory
        self.tiktok_cookie = tiktok_cookie.strip()
        self.douyin_cookie = douyin_cookie.strip()
        self.tiktok_proxy = tiktok_proxy.strip()
        self.douyin_proxy = douyin_proxy.strip()
        self._active_index = 0
        self._total_items = 1

    @Slot()
    def run(self) -> None:
        try:
            result = self._download()
        except Exception as exc:
            self.failed.emit(self._friendly_error(exc))
            return
        self.finished.emit(result)

    def _download(self) -> dict[str, Any]:
        urls = self.extract_urls(self.text)
        if not urls:
            raise ValueError("Paste at least one complete TikTok or Douyin link.")

        output = Path(self.output_directory).expanduser().resolve()
        output.mkdir(parents=True, exist_ok=True)

        selected_platform = self.platform.lower().strip()
        if selected_platform not in {"auto", "tiktok", "douyin"}:
            selected_platform = "auto"

        self._total_items = len(urls)
        self.progress.emit(0)
        self.status.emit(f"Preparing {len(urls)} download(s)…")
        self.log.emit("Download engine: yt-dlp")
        self.log.emit(f"Save folder: {output}")

        results: list[dict[str, Any]] = []
        for index, url in enumerate(urls, start=1):
            self._active_index = index
            detected = self.detect_platform(url, selected_platform)
            self.item_started.emit(index, len(urls), url, detected)
            self.status.emit(f"Downloading item {index} of {len(urls)}…")
            self.log.emit(f"[{index}/{len(urls)}] {url}")

            info = self._download_one(url, detected, output)
            title = str(info.get("title") or info.get("id") or "Downloaded item")
            self.item_title.emit(index, title)
            self.item_progress.emit(index, 100, "Completed")

            filename = self._resolve_filename(info)
            results.append(
                {
                    "id": str(info.get("id") or ""),
                    "title": title,
                    "platform": detected,
                    "url": url,
                    "filename": filename,
                }
            )
            self.log.emit(f"Completed: {title}")

        self.progress.emit(100)
        self.status.emit("All downloads complete")
        return {
            "platform": selected_platform,
            "count": len(results),
            "output_directory": str(output),
            "results": results,
        }

    def _download_one(self, url: str, platform: str, output: Path) -> dict[str, Any]:
        cookie = self.tiktok_cookie if platform == "tiktok" else self.douyin_cookie
        proxy = self.tiktok_proxy if platform == "tiktok" else self.douyin_proxy

        options: dict[str, Any] = {
            "format": "best[ext=mp4]/best",
            "paths": {"home": str(output)},
            "outtmpl": "%(uploader|Unknown)s - %(title).120B [%(id)s].%(ext)s",
            "windowsfilenames": True,
            "noplaylist": True,
            "continuedl": True,
            "overwrites": False,
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
                raise RuntimeError("The downloader did not return media information.")
            return info

    def _progress_hook(self, data: dict[str, Any]) -> None:
        status = str(data.get("status") or "")
        if status == "downloading":
            downloaded = int(data.get("downloaded_bytes") or 0)
            total = int(data.get("total_bytes") or data.get("total_bytes_estimate") or 0)
            item_percent = int(downloaded * 100 / total) if total else 0
            item_percent = max(0, min(item_percent, 99))
            speed = self._human_speed(data.get("speed"))
            eta = data.get("eta")
            detail = "Downloading"
            if speed:
                detail += f" · {speed}"
            if eta is not None:
                detail += f" · {int(eta)}s left"
            self.item_progress.emit(self._active_index, item_percent, detail)
            overall = int(
                ((self._active_index - 1) + (item_percent / 100))
                / self._total_items
                * 100
            )
            self.progress.emit(max(1, min(overall, 99)))
        elif status == "finished":
            filename = Path(str(data.get("filename") or "")).name
            self.item_progress.emit(self._active_index, 99, "Finalizing")
            if filename:
                self.log.emit(f"Saved media: {filename}")

    @staticmethod
    def _resolve_filename(info: dict[str, Any]) -> str:
        requested = info.get("requested_downloads") or []
        if requested and isinstance(requested[0], dict):
            return str(requested[0].get("filepath") or "")
        return str(info.get("_filename") or "")

    @staticmethod
    def _human_speed(value: Any) -> str:
        try:
            speed = float(value)
        except (TypeError, ValueError):
            return ""
        units = ("B/s", "KB/s", "MB/s", "GB/s")
        unit = units[0]
        for unit in units:
            if speed < 1024 or unit == units[-1]:
                break
            speed /= 1024
        return f"{speed:.1f} {unit}"

    @staticmethod
    def extract_urls(text: str) -> list[str]:
        urls: list[str] = []
        for match in URL_PATTERN.findall(text):
            url = match.rstrip(".,;:!?)]}")
            lowered = url.lower()
            if (
                "tiktok.com" not in lowered
                and "douyin.com" not in lowered
                and "iesdouyin.com" not in lowered
            ):
                continue
            if url not in urls:
                urls.append(url)
        return urls

    @staticmethod
    def detect_platform(text: str, selected: str = "auto") -> str:
        selected = selected.lower().strip()
        if selected in {"tiktok", "douyin"}:
            return selected
        lowered = text.lower()
        if "tiktok.com" in lowered:
            return "tiktok"
        if "douyin.com" in lowered or "iesdouyin.com" in lowered:
            return "douyin"
        raise ValueError("Could not detect the platform. Select it manually.")

    @staticmethod
    def _friendly_error(exc: Exception) -> str:
        message = str(exc).strip() or type(exc).__name__
        if isinstance(exc, DownloadError):
            message = re.sub(r"^ERROR:\s*", "", message)
            lowered = message.lower()
            if "login" in lowered or "sign in" in lowered or "cookies" in lowered:
                return (
                    f"{message}\n\nThis post may require login. Open Settings and paste "
                    "a fresh Cookie from your own TikTok/Douyin browser session."
                )
            return f"yt-dlp could not download this post:\n{message}"
        return f"{type(exc).__name__}: {message}"
