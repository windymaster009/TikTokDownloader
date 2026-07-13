from __future__ import annotations

import asyncio

from src.application import TikTokDownloader
from src.application.main_server import APIServer
from src.custom import SERVER_HOST, SERVER_PORT


async def run_api() -> None:
    async with TikTokDownloader() as downloader:
        downloader.check_config()
        await downloader.check_settings(False)
        print(f"DouK Web API: http://127.0.0.1:{SERVER_PORT}/docs")
        await APIServer(downloader.parameter, downloader.database).run_server(
            SERVER_HOST,
            SERVER_PORT,
        )


if __name__ == "__main__":
    try:
        asyncio.run(run_api())
    except KeyboardInterrupt:
        pass
