# TikTok Downloader Desktop

The `destop-mod` branch adds a Windows-friendly PySide6 desktop application while keeping the original terminal entry point unchanged.

## Desktop milestone 4

- Sidebar navigation matching the planned desktop layout.
- Home dashboard.
- Direct TikTok and Douyin video/photo-post downloads.
- One or multiple links per batch.
- Real download percentage, speed, ETA, item status, and batch progress.
- Download history saved locally.
- Clipboard link monitor.
- Optional automatic clipboard downloads with a waiting queue.
- Dedicated settings and application-log pages.
- Optional TikTok/Douyin cookies and proxies.
- Open the output folder after completion.
- Native **Accounts** page:
  - Paste profile links directly.
  - Download public TikTok or Douyin account posts.
  - Select a maximum number of posts.
  - No `accounts_urls_tiktok` JSON editing required.
- Native **Collections** page:
  - Paste playlist or collection links directly.
  - Select a maximum number of items.
  - Save each collection into its own folder.
- New **Feature Guide** page explaining original terminal options 1–13, cookie setup, monitoring mode, Web API mode, and why Web UI mode is disabled upstream.
- **Engine Tools** page exposing the original terminal controls:
  - Paste TikTok or Douyin cookies from the clipboard.
  - Open the complete original terminal menu.
  - Enable automatic desktop clipboard monitoring/download mode.
  - Start and stop the local Web API server.
  - Open Swagger or ReDoc API documentation.
  - Enable or disable original-engine works download records.
  - Enable or disable original-engine runtime logs.
  - Change the terminal language.
  - Manage the disclaimer state.
  - Delete original-engine download records.
  - Open `settings.json`, the engine data folder, and the releases page.

Direct-link, account, and collection downloads use `yt-dlp`. This avoids the upstream DouK encrypted-request code that currently returns `Failed to retrieve data` for some TikTok posts. The original DouK code remains available through **Engine Tools** for terminal, API, live, comments, search, hot-list, favorites, and data-collection workflows.

## Update an existing checkout

```powershell
git fetch origin
git checkout destop-mod
git pull origin destop-mod
```

### Run with uv

```powershell
uv sync --no-dev
uv run desktop.py
```

### Run with pip

```powershell
venv\Scripts\activate
python -m pip install -U yt-dlp
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

Most public posts should work without a cookie. When TikTok or Douyin requires login, open **Feature Guide** for the browser steps, then use **Settings** to paste the complete raw Cookie request-header value from your own browser session.

## Important original-terminal behavior

- Terminal account source option **1** reads account URLs already saved in `settings.json`. It returns zero accounts when that list is empty.
- Terminal account source option **2** asks for a profile link manually.
- Terminal option **6** watches the clipboard and automatically downloads detected links.
- Terminal option **7** starts a local developer Web API; `/docs` and `/redoc` are API documentation pages, not the old downloader Web UI.
- Terminal option **8** is intentionally disabled by the upstream project while its Web UI is being rebuilt.

## Current advanced-feature scope

Direct links, account posts, collections/playlists, history, settings, logs, automatic clipboard downloads, terminal tools, engine preferences, and Web API process controls are functional. Native live recording still needs FFmpeg detection and a reliable Stop control. Original-engine comments, search, hot-list, favorites, favorite music, and favorite-folder workflows remain available through the terminal and Web API where the upstream encrypted-request code still works.
