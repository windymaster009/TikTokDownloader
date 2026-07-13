# DouK Downloader Desktop

This branch adds a Windows-friendly PySide6 desktop interface while keeping the original terminal entry point unchanged.

## Included in the first desktop version

- Paste one or more TikTok or Douyin video/photo-post links.
- Detect TikTok or Douyin automatically, with a manual platform override.
- Select and remember a download folder.
- Run downloads outside the UI thread.
- Display status, progress, and activity logs.
- Save optional TikTok/Douyin cookies and proxies locally.
- Open the output folder after a successful download.

## Run with uv

```powershell
uv sync --no-dev
uv run desktop.py
```

## Run with pip

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python desktop.py
```

The first launch can create the project's normal `settings.json` file. Cookie and proxy values entered in the desktop Settings dialog are copied into the existing downloader settings before each download.

## Current scope

The first version supports direct video and photo-post links. Account batch downloads, collections, live downloads, detailed per-file network progress, cancellation, system-tray clipboard monitoring, and a packaged installer can be added in later desktop milestones.
