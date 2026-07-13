<div align="center">
  <img src="./static/images/DouK-Downloader.png" alt="DouK-Downloader" width="220">
  <h1>DouK-Downloader</h1>
  <p><strong>TikTok and Douyin downloader, data collector, live recorder, and API toolkit.</strong></p>
  <p>
    English · <a href="README_EN.md">Detailed English documentation</a> ·
    <a href="README_CN.md">简体中文</a>
  </p>

  <img alt="Python 3.12+" src="https://img.shields.io/badge/Python-3.12%2B-blue?style=flat-square&logo=python">
  <img alt="License GPL-3.0" src="https://img.shields.io/badge/License-GPL--3.0-green?style=flat-square">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-supported-blue?style=flat-square&logo=docker">
</div>

> This repository is a fork of [JoeanAmier/TikTokDownloader](https://github.com/JoeanAmier/TikTokDownloader), now named **DouK-Downloader** upstream. This fork makes the English guide easier to find and follow.

## Important compatibility notice

The upstream project states that its encryption-parameter algorithm has expired and is no longer maintained. Because of that, some TikTok or Douyin collection features may not work until a compatible parameter generator is configured.

Also note:

- The current **Web UI is temporarily unavailable** after a project refactor.
- Terminal mode and Web API mode are still documented.
- Use the project legally and only download content you are authorized to access.

## Features

- Download TikTok and Douyin videos and image posts.
- Download the highest available video quality when supported.
- Batch-download posts from links, accounts, likes, favorites, collections, and mixes.
- Record TikTok and Douyin live streams with `ffmpeg`.
- Save collected data as CSV, XLSX, or SQLite.
- Skip previously downloaded items and support incremental downloads.
- Filter by publication date and custom rules.
- Use proxies and multi-threaded downloading.
- Run as a terminal application, Web API, or Docker container.
- Access automatically generated API documentation.

## Requirements

- Python **3.12 or newer**
- Git
- `ffmpeg` for live-stream recording
- A valid TikTok or Douyin Cookie for features that require login
- [`uv`](https://docs.astral.sh/uv/) is recommended, but regular `pip` also works

## Quick start with `uv` — recommended

### Windows PowerShell

```powershell
git clone https://github.com/windymaster009/TikTokDownloader.git
cd TikTokDownloader

# Install uv when it is not already installed
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

uv sync --no-dev
uv run main.py
```

### macOS or Linux

```bash
git clone https://github.com/windymaster009/TikTokDownloader.git
cd TikTokDownloader

# Install uv when it is not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

uv sync --no-dev
uv run main.py
```

## Quick start with `pip`

### Windows PowerShell

```powershell
git clone https://github.com/windymaster009/TikTokDownloader.git
cd TikTokDownloader

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

If PowerShell blocks activation, run this once in the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### macOS or Linux

```bash
git clone https://github.com/windymaster009/TikTokDownloader.git
cd TikTokDownloader

python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

## First-time setup

1. Start the application.
2. Read and accept the disclaimer shown by the program.
3. Add your TikTok or Douyin Cookie when prompted, or place it in the project configuration.
4. Return to the main menu.
5. Choose **Terminal Mode**.
6. Choose the link, account, collection, live, or data-collection feature you need.

A Cookie normally only needs to be replaced after it expires. Logged-in Cookies may also be required for private accounts and can affect the video quality available to the downloader.

> Never commit personal Cookies, session tokens, or account credentials to GitHub.

## Basic usage

Start the application:

```bash
python main.py
```

Or with `uv`:

```bash
uv run main.py
```

Inside the terminal menu:

- Press `Enter` to return to the previous menu.
- Enter `Q` or `q` to exit.
- Use `Ctrl + C` to safely stop the program or `ffmpeg`.

## Web API mode

Start Web API mode from the program menu. When the API server is running, open:

- `http://127.0.0.1:5555/docs` for Swagger UI
- `http://127.0.0.1:5555/redoc` for ReDoc

Example request:

```python
from httpx import post

headers = {"token": ""}
data = {
    "detail_id": "0123456789",
    "pages": 2,
}

response = post(
    "http://127.0.0.1:5555/douyin/comment",
    json=data,
    headers=headers,
)
print(response.json())
```

## Docker

Pull an image:

```bash
docker pull joeanamier/tiktok-downloader
```

Or:

```bash
docker pull ghcr.io/joeanamier/tiktok-downloader
```

Create and run a container:

```bash
docker run --name tiktok-downloader \
  -p 5555:5555 \
  -v tiktok_downloader_volume:/app/Volume \
  -it joeanamier/tiktok-downloader
```

Restart it later:

```bash
docker start -i tiktok-downloader
```

Docker containers cannot directly access all host-browser data, so browser-Cookie extraction and some desktop-specific features may be unavailable.

## Build an executable with GitHub Actions

1. Open the **Actions** tab in this fork.
2. Enable Actions when GitHub asks for permission.
3. Select the executable-build workflow.
4. Click **Run workflow**.
5. Choose `master` or `develop`.
6. After the workflow finishes, download the generated file from the run's **Artifacts** section.

## Configuration and storage

- Main settings are stored in the project's configuration files, including `settings.json` where applicable.
- Downloaded content and collected data are stored under the project's volume/output directories.
- The downloader uses a temporary directory while downloading, then moves completed files into the final storage directory.
- Previously downloaded item IDs can be recorded so repeat runs can skip them.

Do not run several copies from the same project directory. Copy the whole directory first when multiple independent instances are required.

## Common problems

### Some TikTok or Douyin features fail

The encryption-parameter generator may be missing or incompatible. Review the upstream documentation and current project status before debugging Cookies or network settings.

### The highest video quality is unavailable

Refresh the Cookie and confirm that it belongs to a logged-in account.

### Dependency installation fails

Confirm that Python 3.12 or newer is being used:

```bash
python --version
```

Then recreate the virtual environment and reinstall dependencies.

### PowerShell will not activate the virtual environment

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Live recording does not start

Install `ffmpeg` and confirm it is available:

```bash
ffmpeg -version
```

## Updating this fork

To refresh your local copy:

```bash
git pull
uv sync --no-dev
```

To keep the GitHub fork synchronized with upstream, use GitHub's **Sync fork** button or add the upstream remote locally:

```bash
git remote add upstream https://github.com/JoeanAmier/TikTokDownloader.git
git fetch upstream
git checkout master
git merge upstream/master
git push origin master
```

## Documentation

- [Detailed English README](README_EN.md)
- [Simplified Chinese documentation](README_CN.md)
- [Upstream project documentation](https://github.com/JoeanAmier/TikTokDownloader/wiki/Documentation)
- [Cookie extraction tutorial](https://github.com/JoeanAmier/TikTokDownloader/blob/master/docs/Cookie%E8%8E%B7%E5%8F%96%E6%95%99%E7%A8%8B.md)

## Responsible use

You are responsible for complying with applicable laws, platform terms, privacy rules, and copyright restrictions. Do not use this project to access private data without authorization, bypass access controls, or download and redistribute protected content illegally.

## License and credits

This project is licensed under the **GNU General Public License v3.0**. Keep the original license and attribution when redistributing modified versions.

Original project and primary maintainer:

- [JoeanAmier/TikTokDownloader](https://github.com/JoeanAmier/TikTokDownloader)

This fork:

- [windymaster009/TikTokDownloader](https://github.com/windymaster009/TikTokDownloader)
