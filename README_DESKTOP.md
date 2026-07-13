# TikTok Downloader Desktop

The `destop-mod` branch adds a Windows-friendly PySide6 desktop application while keeping the original terminal entry point unchanged.

## Desktop milestone 3

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
- New **Engine Tools** page exposing the original terminal controls:
  - Paste TikTok or Douyin cookies from the clipboard.
  - Open the complete original terminal menu.
  - Enable desktop clipboard monitoring mode.
  - Start and stop the local Web API server.
  - Open the generated API documentation.
  - Enable or disable original-engine works download records.
  - Enable or disable original-engine runtime logs.
  - Change the terminal language.
  - Manage the disclaimer state.
  - Delete original-engine download records.
  - Open `settings.json`, the engine data folder, and the releases page.

Direct-link downloads use `yt-dlp`. This avoids the upstream DouK encrypted-request code that currently returns `Failed to retrieve data` for some TikTok posts. The original DouK code remains available through **Engine Tools** for terminal, API, account, collection, live, search, and data-collection workflows.

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

Most public posts should work without a cookie. When TikTok or Douyin requires login, use **Engine Tools → Cookie Tools** or open **Settings** in the sidebar and paste a fresh raw Cookie header from your own browser session.

## Current advanced-feature scope

Direct links, history, settings, logs, clipboard monitoring, terminal tools, engine preferences, and Web API process controls are functional. The original terminal remains available for its complete account, collection, live, comment, search, hot-list, and data-collection feature set. Native desktop forms for every advanced workflow and a packaged Windows installer remain planned for later milestones.
