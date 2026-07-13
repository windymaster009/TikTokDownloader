from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot

from src.application import TikTokDownloader
from src.application.main_server import APIServer
from src.models import Detail, DetailTikTok


class DownloadWorker(QObject):
    """Run the existing async downloader engine outside the Qt UI thread."""

    progress = Signal(int)
    status = Signal(str)
    log = Signal(str)
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

    @Slot()
    def run(self) -> None:
        try:
            result = asyncio.run(self._download())
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}")
            return
        self.finished.emit(result)

    async def _download(self) -> dict[str, Any]:
        if not self.text:
            raise ValueError("Paste at least one TikTok or Douyin link.")

        output = Path(self.output_directory).expanduser().resolve()
        output.mkdir(parents=True, exist_ok=True)
        platform = self.detect_platform(self.text, self.platform)

        self.status.emit("Starting downloader engine…")
        self.log.emit(f"Platform: {platform.title()}")
        self.log.emit(f"Save folder: {output}")
        self.progress.emit(2)

        async with TikTokDownloader() as core:
            core.check_config()
            settings = core.settings.read()
            settings["root"] = str(output)

            if self.tiktok_cookie:
                settings["cookie_tiktok"] = self.tiktok_cookie
            if self.douyin_cookie:
                settings["cookie"] = self.douyin_cookie
            if self.tiktok_proxy:
                settings["proxy_tiktok"] = self.tiktok_proxy
            if self.douyin_proxy:
                settings["proxy"] = self.douyin_proxy

            core.settings.update(settings)
            await core.check_settings(False)
            api = APIServer(core.parameter, core.database, server_mode=True)

            if platform == "tiktok":
                proxy = self.tiktok_proxy or settings.get("proxy_tiktok") or None
                detail_ids = await api.links_tiktok.run(self.text, "detail", proxy)
                model = DetailTikTok
            else:
                proxy = self.douyin_proxy or settings.get("proxy") or None
                detail_ids = await api.links.run(self.text, "detail", proxy)
                model = Detail

            detail_ids = list(dict.fromkeys(detail_ids))
            if not detail_ids:
                raise ValueError(
                    "No downloadable video or photo-post link was found. "
                    "Try pasting the complete share link."
                )

            self.log.emit(f"Found {len(detail_ids)} item(s).")
            results: list[Any] = []
            total = len(detail_ids)

            for index, detail_id in enumerate(detail_ids, start=1):
                self.status.emit(f"Downloading item {index} of {total}…")
                self.log.emit(f"Downloading ID: {detail_id}")
                self.progress.emit(5 + int(((index - 1) / total) * 90))

                response = await api.handle_detail(model(detail_id=detail_id))
                if response.data is None:
                    raise RuntimeError(response.message)

                results.append(response.data)
                self.progress.emit(5 + int((index / total) * 90))
                self.log.emit(f"Completed ID: {detail_id}")

        self.progress.emit(100)
        self.status.emit("Download complete")
        return {
            "platform": platform,
            "count": len(results),
            "output_directory": str(output),
            "results": results,
        }

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

        raise ValueError(
            "Could not detect the platform. Select TikTok or Douyin manually."
        )
