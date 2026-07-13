# TikTok Downloader Desktop

The `destop-mod` branch adds a Windows-friendly PySide6 desktop application while keeping the original terminal entry point unchanged.

## Desktop milestone 2

- Sidebar navigation matching the planned desktop layout.
- Home dashboard.
- Direct TikTok and Douyin video/photo-post downloads.
- One or multiple links per batch.
- Real download percentage, speed, ETA, item status, and batch progress.
- Download history saved locally.
- Clipboard link monitor.
- Dedicated settings and application-log pages.
- Optional TikTok/Douyin cookies and proxies.
- Open the output folder after completion.

Direct-link downloads now use `yt-dlp`. This avoids the upstream DouK encrypted-request code that currently returns `Failed to retrieve data` for some TikTok posts. The original DouK code remains in the repository for the advanced account, collection, and live features that will be connected in later milestones.

## Update an existing checkout

```powershell
git fetch origin
git checkout destop-mod
git pull origin destop-mod
```

Then refresh dependencies because milestone 2 adds `yt-dlp`.

### Run with uv

```powershell
uv sync --no-dev
uv run desktop.py
```

### Run with pip

```powershell
venv\Scripts\activate
pip install -r requirements.txt
python desktop.py
```

For a fresh pip environment:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python desktop.py
```

## Cookies

Most public posts should work without a cookie. When TikTok or Douyin requires login, open **Settings** in the sidebar and paste a fresh raw Cookie header from your own browser session.

## Current advanced-feature scope

Direct links, history, settings, logs, and clipboard monitoring are functional. Account batch downloads, collections, live recording, cancellation, and a packaged Windows installer remain planned for later desktop milestones.
