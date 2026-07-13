from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.custom import PROJECT_ROOT, RELEASES

from .main_window import MainWindow as BaseMainWindow


class MainWindow(BaseMainWindow):
    """Desktop milestone 3: expose the original terminal control options in Qt."""

    def __init__(self) -> None:
        super().__init__()
        self._project_root = Path(__file__).resolve().parents[2]
        self._terminal_process: subprocess.Popen | None = None
        self._api_process: subprocess.Popen | None = None

        self._install_tools_page()
        self._load_engine_options()

        self.process_timer = QTimer(self)
        self.process_timer.setInterval(1000)
        self.process_timer.timeout.connect(self._refresh_process_state)
        self.process_timer.start()

    def _install_tools_page(self) -> None:
        self.tools_page = self._build_tools_page()
        self.pages["tools"] = self.tools_page
        self.stack.addWidget(self.tools_page)

        sidebar = self.findChild(QFrame, "sidebar")
        if sidebar is None or sidebar.layout() is None:
            return

        button = QPushButton("⚒  Engine Tools")
        button.setObjectName("navButton")
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda checked=False: self._navigate("tools"))
        self.nav_group.addButton(button)
        self.nav_buttons["tools"] = button

        layout = sidebar.layout()
        # Sidebar ends with an expanding spacer and the version label.
        layout.insertWidget(max(0, layout.count() - 2), button)

    def _build_tools_page(self) -> QWidget:
        page, layout = self._page_container()

        modes, modes_layout = self._card()
        modes_title = QLabel("Original Engine Modes")
        modes_title.setObjectName("sectionTitle")
        modes_layout.addWidget(modes_title)
        modes_note = QLabel(
            "These controls expose the modes from the original terminal menu. "
            "They run separately so the desktop downloader remains responsive."
        )
        modes_note.setObjectName("muted")
        modes_note.setWordWrap(True)
        modes_layout.addWidget(modes_note)

        mode_grid = QGridLayout()
        mode_grid.setHorizontalSpacing(12)
        mode_grid.setVerticalSpacing(10)
        terminal = QPushButton("Open Original Terminal")
        terminal.setObjectName("primary")
        terminal.clicked.connect(self.open_terminal_mode)
        mode_grid.addWidget(terminal, 0, 0)

        monitor = QPushButton("Open Monitoring Mode")
        monitor.clicked.connect(self.open_monitoring_mode)
        mode_grid.addWidget(monitor, 0, 1)

        self.api_button = QPushButton("Start Web API")
        self.api_button.clicked.connect(self.toggle_api_server)
        mode_grid.addWidget(self.api_button, 1, 0)

        docs = QPushButton("Open API Documentation")
        docs.clicked.connect(self.open_api_docs)
        mode_grid.addWidget(docs, 1, 1)

        web_ui = QPushButton("Web UI Mode — unavailable upstream")
        web_ui.setEnabled(False)
        mode_grid.addWidget(web_ui, 2, 0, 1, 2)
        modes_layout.addLayout(mode_grid)
        self.api_status = QLabel("Web API stopped")
        self.api_status.setObjectName("muted")
        modes_layout.addWidget(self.api_status)
        layout.addWidget(modes)

        cookies, cookies_layout = self._card()
        cookie_title = QLabel("Cookie Tools")
        cookie_title.setObjectName("sectionTitle")
        cookies_layout.addWidget(cookie_title)
        cookie_note = QLabel(
            "Equivalent to terminal options 1–4. Paste cookies only from your own "
            "TikTok or Douyin browser session."
        )
        cookie_note.setObjectName("muted")
        cookie_note.setWordWrap(True)
        cookies_layout.addWidget(cookie_note)

        cookie_row = QHBoxLayout()
        tiktok_cookie = QPushButton("Paste TikTok Cookie")
        tiktok_cookie.clicked.connect(lambda: self.paste_cookie("tiktok"))
        cookie_row.addWidget(tiktok_cookie)
        douyin_cookie = QPushButton("Paste Douyin Cookie")
        douyin_cookie.clicked.connect(lambda: self.paste_cookie("douyin"))
        cookie_row.addWidget(douyin_cookie)
        edit_cookies = QPushButton("Edit Cookies / Proxies")
        edit_cookies.clicked.connect(lambda: self._navigate("settings"))
        cookie_row.addWidget(edit_cookies)
        cookie_row.addStretch(1)
        cookies_layout.addLayout(cookie_row)
        layout.addWidget(cookies)

        preferences, preferences_layout = self._card()
        preference_title = QLabel("Original Engine Preferences")
        preference_title.setObjectName("sectionTitle")
        preferences_layout.addWidget(preference_title)
        preference_note = QLabel(
            "Controls the DouK engine database settings used by terminal mode: "
            "download records, runtime logs, disclaimer state, and language."
        )
        preference_note.setObjectName("muted")
        preference_note.setWordWrap(True)
        preferences_layout.addWidget(preference_note)

        preference_grid = QGridLayout()
        self.engine_record = QCheckBox("Enable works download history")
        self.engine_logger = QCheckBox("Enable runtime log history")
        self.engine_disclaimer = QCheckBox("Disclaimer already accepted")
        self.engine_language = QComboBox()
        self.engine_language.addItem("English", "en_US")
        self.engine_language.addItem("Simplified Chinese", "zh_CN")
        preference_grid.addWidget(self.engine_record, 0, 0)
        preference_grid.addWidget(self.engine_logger, 0, 1)
        preference_grid.addWidget(self.engine_disclaimer, 1, 0)
        preference_grid.addWidget(QLabel("Terminal language"), 1, 1)
        preference_grid.addWidget(self.engine_language, 1, 2)
        preferences_layout.addLayout(preference_grid)

        preference_actions = QHBoxLayout()
        save = QPushButton("Save Engine Preferences")
        save.setObjectName("primary")
        save.clicked.connect(self.save_engine_options)
        preference_actions.addWidget(save)
        reload_button = QPushButton("Reload")
        reload_button.clicked.connect(self._load_engine_options)
        preference_actions.addWidget(reload_button)
        preference_actions.addStretch(1)
        preferences_layout.addLayout(preference_actions)
        layout.addWidget(preferences)

        maintenance, maintenance_layout = self._card()
        maintenance_title = QLabel("Maintenance")
        maintenance_title.setObjectName("sectionTitle")
        maintenance_layout.addWidget(maintenance_title)
        maintenance_row = QHBoxLayout()
        delete_records = QPushButton("Delete Engine Download Records")
        delete_records.setObjectName("danger")
        delete_records.clicked.connect(self.delete_engine_records)
        maintenance_row.addWidget(delete_records)
        update = QPushButton("Check for Updates")
        update.clicked.connect(self.open_releases)
        maintenance_row.addWidget(update)
        open_settings = QPushButton("Open settings.json")
        open_settings.clicked.connect(self.open_engine_settings)
        maintenance_row.addWidget(open_settings)
        open_volume = QPushButton("Open Engine Data Folder")
        open_volume.clicked.connect(self.open_engine_folder)
        maintenance_row.addWidget(open_volume)
        maintenance_row.addStretch(1)
        maintenance_layout.addLayout(maintenance_row)
        layout.addWidget(maintenance)

        layout.addStretch(1)
        return page

    def _navigate(self, key: str) -> None:
        if key != "tools":
            super()._navigate(key)
            return
        self.stack.setCurrentWidget(self.tools_page)
        self.nav_buttons["tools"].setChecked(True)
        self.page_title.setText("Engine Tools")
        self.page_subtitle.setText("Original terminal modes, cookies, records, logs, API, and updates")

    @property
    def _database_path(self) -> Path:
        return PROJECT_ROOT / "DouK-Downloader.db"

    @staticmethod
    def _new_console_flags() -> int:
        return subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0

    def _start_process(self, script: Path) -> subprocess.Popen:
        if not script.exists():
            raise FileNotFoundError(f"Required launcher was not found: {script}")
        return subprocess.Popen(
            [sys.executable, str(script)],
            cwd=str(self._project_root),
            creationflags=self._new_console_flags(),
        )

    def open_terminal_mode(self) -> None:
        try:
            if self._terminal_process and self._terminal_process.poll() is None:
                QMessageBox.information(
                    self, "Original terminal", "The original terminal is already running."
                )
                return
            self._terminal_process = self._start_process(self._project_root / "main.py")
            self.append_log("Opened the original DouK terminal menu.")
            self.header_status.setText("Terminal opened")
        except Exception as exc:
            QMessageBox.critical(self, "Terminal error", str(exc))

    def open_monitoring_mode(self) -> None:
        self.clipboard_toggle.setChecked(True)
        self._navigate("clipboard")
        self.header_status.setText("Clipboard monitoring enabled")

    def toggle_api_server(self) -> None:
        try:
            if self._api_process and self._api_process.poll() is None:
                self._api_process.terminate()
                self._api_process = None
                self._refresh_process_state()
                self.append_log("Stopped the local Web API server.")
                return
            self._api_process = self._start_process(self._project_root / "desktop_api.py")
            self.append_log("Started the local Web API server on port 5555.")
            self.api_status.setText("Web API starting…")
            self.api_button.setText("Stop Web API")
        except Exception as exc:
            QMessageBox.critical(self, "Web API error", str(exc))

    def _refresh_process_state(self) -> None:
        running = bool(self._api_process and self._api_process.poll() is None)
        self.api_button.setText("Stop Web API" if running else "Start Web API")
        self.api_status.setText(
            "Web API running · http://127.0.0.1:5555/docs"
            if running
            else "Web API stopped"
        )
        if self._api_process and not running:
            self._api_process = None

    def open_api_docs(self) -> None:
        QDesktopServices.openUrl(QUrl("http://127.0.0.1:5555/docs"))

    def paste_cookie(self, platform: str) -> None:
        cookie = QApplication.clipboard().text().strip()
        if not cookie:
            QMessageBox.information(self, "Cookie", "The clipboard is empty.")
            return
        if platform == "tiktok":
            self.tiktok_cookie.setPlainText(cookie)
        else:
            self.douyin_cookie.setPlainText(cookie)
        self.save_settings()
        self._navigate("settings")
        self.header_status.setText(f"{platform.title()} cookie saved")

    def _ensure_engine_database(self) -> sqlite3.Connection:
        PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._database_path)
        connection.execute(
            "CREATE TABLE IF NOT EXISTS config_data ("
            "NAME TEXT PRIMARY KEY, VALUE INTEGER NOT NULL CHECK(VALUE IN (0, 1)))"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS option_data ("
            "NAME TEXT PRIMARY KEY, VALUE TEXT NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS download_data (ID TEXT PRIMARY KEY)"
        )
        connection.executemany(
            "INSERT OR IGNORE INTO config_data (NAME, VALUE) VALUES (?, ?)",
            (("Record", 1), ("Logger", 0), ("Disclaimer", 0)),
        )
        connection.execute(
            "INSERT OR IGNORE INTO option_data (NAME, VALUE) VALUES ('Language', 'zh_CN')"
        )
        connection.commit()
        return connection

    def _load_engine_options(self) -> None:
        try:
            with self._ensure_engine_database() as connection:
                config = dict(connection.execute("SELECT NAME, VALUE FROM config_data"))
                options = dict(connection.execute("SELECT NAME, VALUE FROM option_data"))
            self.engine_record.setChecked(bool(config.get("Record", 1)))
            self.engine_logger.setChecked(bool(config.get("Logger", 0)))
            self.engine_disclaimer.setChecked(bool(config.get("Disclaimer", 0)))
            language = str(options.get("Language", "zh_CN"))
            index = self.engine_language.findData(language)
            self.engine_language.setCurrentIndex(max(0, index))
        except Exception as exc:
            self.append_log(f"Could not load engine preferences: {exc}")

    def save_engine_options(self) -> None:
        try:
            with self._ensure_engine_database() as connection:
                connection.executemany(
                    "REPLACE INTO config_data (NAME, VALUE) VALUES (?, ?)",
                    (
                        ("Record", int(self.engine_record.isChecked())),
                        ("Logger", int(self.engine_logger.isChecked())),
                        ("Disclaimer", int(self.engine_disclaimer.isChecked())),
                    ),
                )
                connection.execute(
                    "REPLACE INTO option_data (NAME, VALUE) VALUES ('Language', ?)",
                    (str(self.engine_language.currentData()),),
                )
                connection.commit()
            self.header_status.setText("Engine preferences saved")
            self.append_log("Original DouK engine preferences saved.")
        except Exception as exc:
            QMessageBox.critical(self, "Engine settings error", str(exc))

    def delete_engine_records(self) -> None:
        answer = QMessageBox.question(
            self,
            "Delete engine records",
            "Delete all original DouK works-download records?\n\n"
            "Downloaded media files will not be deleted.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            with self._ensure_engine_database() as connection:
                connection.execute("DELETE FROM download_data")
                connection.commit()
            self.append_log("Deleted all original engine download records.")
            self.header_status.setText("Engine records deleted")
        except Exception as exc:
            QMessageBox.critical(self, "Delete records error", str(exc))

    def open_releases(self) -> None:
        QDesktopServices.openUrl(QUrl(RELEASES))

    def open_engine_settings(self) -> None:
        settings_file = PROJECT_ROOT / "settings.json"
        if not settings_file.exists():
            settings_file.write_text("{}\n", encoding="utf-8")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(settings_file)))

    def open_engine_folder(self) -> None:
        PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(PROJECT_ROOT)))

    def closeEvent(self, event) -> None:
        super().closeEvent(event)
        if event.isAccepted() and self._api_process and self._api_process.poll() is None:
            self._api_process.terminate()
