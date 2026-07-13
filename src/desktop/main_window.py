from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSettings, QThread, QTimer, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .service import DownloadWorker


APP_STYLE = """
QMainWindow {
    background: #0b1220;
}
QWidget {
    color: #dbe7f5;
    font-family: "Segoe UI";
    font-size: 13px;
}
QFrame#sidebar {
    background: #07101d;
    border-right: 1px solid #1e2a3d;
}
QLabel#brandMark {
    background: #2563eb;
    color: white;
    border-radius: 10px;
    font-size: 17px;
    font-weight: 800;
    qproperty-alignment: AlignCenter;
}
QLabel#brandTitle {
    color: #f8fafc;
    font-size: 17px;
    font-weight: 750;
}
QLabel#brandCaption, QLabel#muted, QLabel#pageSubtitle, QLabel#cardCaption {
    color: #8391a7;
}
QPushButton#navButton {
    background: transparent;
    border: none;
    border-radius: 9px;
    color: #9dacbf;
    font-size: 14px;
    font-weight: 600;
    padding: 11px 13px;
    text-align: left;
}
QPushButton#navButton:hover {
    background: #111c2f;
    color: #e8f0fb;
}
QPushButton#navButton:checked {
    background: #1d4ed8;
    color: white;
}
QFrame#contentHeader {
    background: transparent;
    border-bottom: 1px solid #1f2b3e;
}
QLabel#pageTitle {
    color: #f8fafc;
    font-size: 25px;
    font-weight: 750;
}
QLabel#sectionTitle {
    color: #f8fafc;
    font-size: 16px;
    font-weight: 700;
}
QLabel#metricValue {
    color: #f8fafc;
    font-size: 23px;
    font-weight: 750;
}
QFrame#card, QFrame#metricCard {
    background: #101a2d;
    border: 1px solid #24324a;
    border-radius: 13px;
}
QPlainTextEdit, QLineEdit, QComboBox {
    background: #091323;
    border: 1px solid #30415f;
    border-radius: 8px;
    padding: 9px;
    selection-background-color: #2563eb;
}
QPlainTextEdit:focus, QLineEdit:focus, QComboBox:focus {
    border: 1px solid #4f8cff;
}
QPushButton {
    background: #18263b;
    border: 1px solid #30415a;
    border-radius: 8px;
    color: #e4edf8;
    padding: 9px 14px;
    font-weight: 650;
}
QPushButton:hover {
    background: #21324b;
}
QPushButton#primary {
    background: #2563eb;
    border-color: #3b82f6;
    color: white;
}
QPushButton#primary:hover {
    background: #1d4ed8;
}
QPushButton#danger {
    background: #3a1720;
    border-color: #71303c;
    color: #fecdd3;
}
QPushButton:disabled {
    background: #152135;
    border-color: #26354c;
    color: #60718a;
}
QProgressBar {
    background: #08111f;
    border: 1px solid #2a3b56;
    border-radius: 6px;
    min-height: 12px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: #3b82f6;
    border-radius: 5px;
}
QTableWidget {
    background: #0c1628;
    alternate-background-color: #101b2e;
    border: 1px solid #24324a;
    border-radius: 9px;
    gridline-color: #1d2a40;
    selection-background-color: #1e3a66;
    selection-color: white;
}
QHeaderView::section {
    background: #111d31;
    color: #9fb0c6;
    border: none;
    border-bottom: 1px solid #293852;
    padding: 9px;
    font-weight: 700;
}
QCheckBox {
    spacing: 9px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
}
"""


class MainWindow(QMainWindow):
    NAV_ITEMS = (
        ("home", "⌂  Home"),
        ("download", "⇩  Download"),
        ("accounts", "●  Accounts"),
        ("collections", "▣  Collections"),
        ("live", "◉  Live"),
        ("history", "◷  History"),
        ("clipboard", "▤  Clipboard"),
        ("settings", "⚙  Settings"),
        ("logs", "≡  Logs"),
    )

    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings("WindyMaster", "TikTokDownloaderDesktop")
        self._thread: QThread | None = None
        self._worker: DownloadWorker | None = None
        self._last_output_directory = ""
        self._last_clipboard = ""
        self._download_rows: dict[int, int] = {}
        self._download_bars: dict[int, QProgressBar] = {}
        self.history = self._load_history()

        self.setWindowTitle("TikTok Downloader")
        self.resize(1180, 760)
        self.setMinimumSize(980, 650)
        self.setStyleSheet(APP_STYLE)

        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setCentralWidget(central)

        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_content(), 1)

        self.clipboard_timer = QTimer(self)
        self.clipboard_timer.setInterval(1000)
        self.clipboard_timer.timeout.connect(self._check_clipboard)
        self._apply_clipboard_monitor_state()

        self._refresh_history_table()
        self._refresh_home()
        self._navigate("download")

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 20, 18, 18)
        layout.setSpacing(7)

        brand_row = QHBoxLayout()
        mark = QLabel("TD")
        mark.setObjectName("brandMark")
        mark.setFixedSize(42, 42)
        brand_row.addWidget(mark)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)
        title = QLabel("TikTok Downloader")
        title.setObjectName("brandTitle")
        caption = QLabel("Desktop Edition")
        caption.setObjectName("brandCaption")
        brand_text.addWidget(title)
        brand_text.addWidget(caption)
        brand_row.addLayout(brand_text, 1)
        layout.addLayout(brand_row)
        layout.addSpacing(18)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons: dict[str, QPushButton] = {}
        for key, text in self.NAV_ITEMS:
            button = QPushButton(text)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False, page=key: self._navigate(page))
            self.nav_group.addButton(button)
            self.nav_buttons[key] = button
            layout.addWidget(button)

        layout.addStretch(1)
        version = QLabel("DouK engine + yt-dlp\nDesktop milestone 2")
        version.setObjectName("muted")
        version.setWordWrap(True)
        layout.addWidget(version)
        return sidebar

    def _build_content(self) -> QWidget:
        shell = QWidget()
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("contentHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(28, 18, 28, 16)
        titles = QVBoxLayout()
        titles.setSpacing(2)
        self.page_title = QLabel("Download")
        self.page_title.setObjectName("pageTitle")
        self.page_subtitle = QLabel("Download TikTok and Douyin videos or photo posts")
        self.page_subtitle.setObjectName("pageSubtitle")
        titles.addWidget(self.page_title)
        titles.addWidget(self.page_subtitle)
        header_layout.addLayout(titles)
        header_layout.addStretch(1)
        self.header_status = QLabel("Ready")
        self.header_status.setObjectName("muted")
        header_layout.addWidget(self.header_status)
        layout.addWidget(header)

        self.stack = QStackedWidget()
        self.pages: dict[str, QWidget] = {
            "home": self._build_home_page(),
            "download": self._build_download_page(),
            "accounts": self._build_placeholder_page(
                "Account downloads",
                "Batch download posts from TikTok or Douyin accounts.",
                "This engine is being wired next. Direct video and photo-post downloads are already available on the Download page.",
            ),
            "collections": self._build_placeholder_page(
                "Collections and playlists",
                "Download a complete playlist or collection from one link.",
                "Collection support will use the original project parser after its current encrypted-request dependency is replaced.",
            ),
            "live": self._build_placeholder_page(
                "Live streams",
                "Resolve live-stream URLs and record supported streams.",
                "Live recording needs FFmpeg detection and stop controls, so it remains disabled in this milestone.",
            ),
            "history": self._build_history_page(),
            "clipboard": self._build_clipboard_page(),
            "settings": self._build_settings_page(),
            "logs": self._build_logs_page(),
        }
        for key, _ in self.NAV_ITEMS:
            self.stack.addWidget(self.pages[key])
        layout.addWidget(self.stack, 1)
        return shell

    def _page_container(self) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 26)
        layout.setSpacing(18)
        return page, layout

    def _card(self) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(12)
        return card, layout

    def _build_home_page(self) -> QWidget:
        page, layout = self._page_container()
        metrics = QGridLayout()
        metrics.setSpacing(14)
        self.home_total = QLabel("0")
        self.home_today = QLabel("0")
        self.home_last = QLabel("Ready")
        metrics.addWidget(
            self._metric_card("Total downloads", self.home_total, "Saved in desktop history"),
            0,
            0,
        )
        metrics.addWidget(
            self._metric_card("Downloaded today", self.home_today, "Completed items today"),
            0,
            1,
        )
        metrics.addWidget(
            self._metric_card("Downloader status", self.home_last, "Latest desktop activity"),
            0,
            2,
        )
        layout.addLayout(metrics)

        quick, quick_layout = self._card()
        title = QLabel("Quick download")
        title.setObjectName("sectionTitle")
        quick_layout.addWidget(title)
        caption = QLabel(
            "Paste a TikTok or Douyin link and start from the dedicated Download workspace."
        )
        caption.setObjectName("cardCaption")
        caption.setWordWrap(True)
        quick_layout.addWidget(caption)
        go = QPushButton("Open Download")
        go.setObjectName("primary")
        go.setFixedWidth(150)
        go.clicked.connect(lambda: self._navigate("download"))
        quick_layout.addWidget(go, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(quick)

        recent, recent_layout = self._card()
        recent_title = QLabel("Recent activity")
        recent_title.setObjectName("sectionTitle")
        recent_layout.addWidget(recent_title)
        self.home_recent = QLabel("No downloads yet.")
        self.home_recent.setObjectName("muted")
        self.home_recent.setWordWrap(True)
        recent_layout.addWidget(self.home_recent)
        layout.addWidget(recent)
        layout.addStretch(1)
        return page

    def _metric_card(self, title: str, value: QLabel, caption: str) -> QFrame:
        card = QFrame()
        card.setObjectName("metricCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        label = QLabel(title)
        label.setObjectName("cardCaption")
        value.setObjectName("metricValue")
        value.setWordWrap(True)
        note = QLabel(caption)
        note.setObjectName("muted")
        layout.addWidget(label)
        layout.addWidget(value)
        layout.addWidget(note)
        return card

    def _build_download_page(self) -> QWidget:
        page, layout = self._page_container()

        input_card, input_layout = self._card()
        heading = QLabel("Download TikTok / Douyin")
        heading.setObjectName("sectionTitle")
        input_layout.addWidget(heading)

        self.link_input = QPlainTextEdit()
        self.link_input.setPlaceholderText(
            "Paste TikTok or Douyin links here…\n"
            "You can paste multiple links or the full share message."
        )
        self.link_input.setMinimumHeight(112)
        input_layout.addWidget(self.link_input)

        options = QHBoxLayout()
        options.setSpacing(10)
        options.addWidget(QLabel("Platform"))
        self.platform_combo = QComboBox()
        self.platform_combo.addItem("Auto detect", "auto")
        self.platform_combo.addItem("TikTok", "tiktok")
        self.platform_combo.addItem("Douyin", "douyin")
        self.platform_combo.setMinimumWidth(150)
        options.addWidget(self.platform_combo)
        options.addSpacing(10)
        options.addWidget(QLabel("Save to"))
        self.folder_edit = QLineEdit()
        default_folder = str(Path.home() / "Downloads" / "TikTok-Downloader")
        self.folder_edit.setText(
            self.settings.value("output_directory", default_folder, str)
        )
        self.folder_edit.setPlaceholderText("Choose a download folder")
        options.addWidget(self.folder_edit, 1)
        browse = QPushButton("Browse")
        browse.clicked.connect(self.choose_folder)
        options.addWidget(browse)
        input_layout.addLayout(options)

        actions = QHBoxLayout()
        paste = QPushButton("Paste Clipboard")
        paste.clicked.connect(self.paste_clipboard)
        actions.addWidget(paste)
        actions.addStretch(1)
        self.download_button = QPushButton("Download")
        self.download_button.setObjectName("primary")
        self.download_button.setMinimumWidth(130)
        self.download_button.clicked.connect(self.start_download)
        actions.addWidget(self.download_button)
        input_layout.addLayout(actions)
        layout.addWidget(input_card)

        current_card, current_layout = self._card()
        current_header = QHBoxLayout()
        current_title = QLabel("Current Downloads")
        current_title.setObjectName("sectionTitle")
        current_header.addWidget(current_title)
        current_header.addStretch(1)
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("muted")
        current_header.addWidget(self.status_label)
        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.setEnabled(False)
        self.open_folder_button.clicked.connect(self.open_output_folder)
        current_header.addWidget(self.open_folder_button)
        current_layout.addLayout(current_header)

        self.batch_progress = QProgressBar()
        self.batch_progress.setRange(0, 100)
        self.batch_progress.setValue(0)
        self.batch_progress.setTextVisible(False)
        current_layout.addWidget(self.batch_progress)

        self.current_table = QTableWidget(0, 4)
        self.current_table.setHorizontalHeaderLabels(
            ("Name / Link", "Platform", "Status", "Progress")
        )
        self.current_table.verticalHeader().setVisible(False)
        self.current_table.setAlternatingRowColors(True)
        self.current_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.current_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.current_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.current_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.current_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.current_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Fixed
        )
        self.current_table.setColumnWidth(3, 170)
        self.current_table.setMinimumHeight(180)
        current_layout.addWidget(self.current_table)
        layout.addWidget(current_card, 1)
        return page

    def _build_placeholder_page(self, title: str, subtitle: str, detail: str) -> QWidget:
        page, layout = self._page_container()
        card, card_layout = self._card()
        heading = QLabel(title)
        heading.setObjectName("sectionTitle")
        card_layout.addWidget(heading)
        intro = QLabel(subtitle)
        intro.setWordWrap(True)
        card_layout.addWidget(intro)
        note = QLabel(detail)
        note.setObjectName("muted")
        note.setWordWrap(True)
        card_layout.addWidget(note)
        badge = QLabel("Planned for the next desktop milestone")
        badge.setStyleSheet(
            "background:#172554; color:#bfdbfe; border:1px solid #1d4ed8; "
            "border-radius:7px; padding:8px 10px;"
        )
        badge.setFixedWidth(285)
        card_layout.addWidget(badge)
        layout.addWidget(card)
        layout.addStretch(1)
        return page

    def _build_history_page(self) -> QWidget:
        page, layout = self._page_container()
        card, card_layout = self._card()
        header = QHBoxLayout()
        title = QLabel("Download History")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch(1)
        open_button = QPushButton("Open Selected Folder")
        open_button.clicked.connect(self.open_selected_history_folder)
        header.addWidget(open_button)
        clear_button = QPushButton("Clear History")
        clear_button.setObjectName("danger")
        clear_button.clicked.connect(self.clear_history)
        header.addWidget(clear_button)
        card_layout.addLayout(header)

        self.history_table = QTableWidget(0, 5)
        self.history_table.setHorizontalHeaderLabels(
            ("Time", "Title", "Platform", "Status", "Folder")
        )
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.history_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.history_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.history_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.history_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch
        )
        card_layout.addWidget(self.history_table)
        layout.addWidget(card, 1)
        return page

    def _build_clipboard_page(self) -> QWidget:
        page, layout = self._page_container()
        card, card_layout = self._card()
        title = QLabel("Clipboard Monitor")
        title.setObjectName("sectionTitle")
        card_layout.addWidget(title)
        caption = QLabel(
            "Watch the Windows clipboard for TikTok or Douyin links. Detected "
            "links can be sent directly to the Download page."
        )
        caption.setObjectName("muted")
        caption.setWordWrap(True)
        card_layout.addWidget(caption)

        self.clipboard_toggle = QCheckBox("Enable clipboard monitoring")
        self.clipboard_toggle.setChecked(
            self.settings.value("clipboard_monitor", False, bool)
        )
        self.clipboard_toggle.toggled.connect(self._clipboard_toggled)
        card_layout.addWidget(self.clipboard_toggle)

        self.clipboard_preview = QPlainTextEdit()
        self.clipboard_preview.setReadOnly(True)
        self.clipboard_preview.setPlaceholderText(
            "A detected TikTok or Douyin link will appear here."
        )
        self.clipboard_preview.setMaximumHeight(125)
        card_layout.addWidget(self.clipboard_preview)

        send = QPushButton("Send to Download")
        send.setObjectName("primary")
        send.setFixedWidth(165)
        send.clicked.connect(self.send_clipboard_to_download)
        card_layout.addWidget(send, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(card)
        layout.addStretch(1)
        return page

    def _build_settings_page(self) -> QWidget:
        page, layout = self._page_container()
        card, card_layout = self._card()
        title = QLabel("Cookies and Network")
        title.setObjectName("sectionTitle")
        card_layout.addWidget(title)
        note = QLabel(
            "Most public posts work without cookies. Add a fresh cookie from your "
            "own browser session only when TikTok or Douyin requires login."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        card_layout.addWidget(note)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        grid.addWidget(QLabel("TikTok Cookie"), 0, 0)
        self.tiktok_cookie = QPlainTextEdit()
        self.tiktok_cookie.setPlaceholderText("Optional raw Cookie header")
        self.tiktok_cookie.setPlainText(
            self.settings.value("tiktok_cookie", "", str)
        )
        self.tiktok_cookie.setMaximumHeight(95)
        grid.addWidget(self.tiktok_cookie, 1, 0)
        grid.addWidget(QLabel("Douyin Cookie"), 0, 1)
        self.douyin_cookie = QPlainTextEdit()
        self.douyin_cookie.setPlaceholderText("Optional raw Cookie header")
        self.douyin_cookie.setPlainText(
            self.settings.value("douyin_cookie", "", str)
        )
        self.douyin_cookie.setMaximumHeight(95)
        grid.addWidget(self.douyin_cookie, 1, 1)
        grid.addWidget(QLabel("TikTok Proxy"), 2, 0)
        self.tiktok_proxy = QLineEdit(
            self.settings.value("tiktok_proxy", "", str)
        )
        self.tiktok_proxy.setPlaceholderText("Example: http://127.0.0.1:7890")
        grid.addWidget(self.tiktok_proxy, 3, 0)
        grid.addWidget(QLabel("Douyin Proxy"), 2, 1)
        self.douyin_proxy = QLineEdit(
            self.settings.value("douyin_proxy", "", str)
        )
        self.douyin_proxy.setPlaceholderText("Example: http://127.0.0.1:7890")
        grid.addWidget(self.douyin_proxy, 3, 1)
        card_layout.addLayout(grid)

        save = QPushButton("Save Settings")
        save.setObjectName("primary")
        save.setFixedWidth(145)
        save.clicked.connect(self.save_settings)
        card_layout.addWidget(save, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(card)
        layout.addStretch(1)
        return page

    def _build_logs_page(self) -> QWidget:
        page, layout = self._page_container()
        card, card_layout = self._card()
        header = QHBoxLayout()
        title = QLabel("Application Logs")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch(1)
        clear = QPushButton("Clear")
        clear.clicked.connect(lambda: self.log_output.clear())
        header.addWidget(clear)
        card_layout.addLayout(header)
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText(
            "Downloader activity and errors will appear here."
        )
        card_layout.addWidget(self.log_output)
        layout.addWidget(card, 1)
        return page

    def _navigate(self, key: str) -> None:
        if key not in self.pages:
            return
        index = [item[0] for item in self.NAV_ITEMS].index(key)
        self.stack.setCurrentIndex(index)
        self.nav_buttons[key].setChecked(True)
        titles = {
            "home": ("Home", "Overview and recent downloader activity"),
            "download": (
                "Download",
                "Download TikTok and Douyin videos or photo posts",
            ),
            "accounts": ("Accounts", "Batch account-post downloads"),
            "collections": ("Collections", "Playlists and collection downloads"),
            "live": ("Live", "Live-stream tools and recording"),
            "history": ("History", "Completed desktop downloads"),
            "clipboard": ("Clipboard", "Detect links copied from your browser"),
            "settings": (
                "Settings",
                "Cookies, proxies, and downloader preferences",
            ),
            "logs": ("Logs", "Detailed downloader output and errors"),
        }
        title, subtitle = titles[key]
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)

    def choose_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Choose download folder",
            self.folder_edit.text() or str(Path.home()),
        )
        if selected:
            self.folder_edit.setText(selected)

    def paste_clipboard(self) -> None:
        text = QApplication.clipboard().text().strip()
        if text:
            current = self.link_input.toPlainText().strip()
            self.link_input.setPlainText(f"{current}\n{text}".strip())

    def save_settings(self) -> None:
        self.settings.setValue(
            "tiktok_cookie", self.tiktok_cookie.toPlainText().strip()
        )
        self.settings.setValue(
            "douyin_cookie", self.douyin_cookie.toPlainText().strip()
        )
        self.settings.setValue("tiktok_proxy", self.tiktok_proxy.text().strip())
        self.settings.setValue("douyin_proxy", self.douyin_proxy.text().strip())
        self.settings.sync()
        self.header_status.setText("Settings saved")
        self.append_log("Desktop settings saved.")

    def start_download(self) -> None:
        if self._thread and self._thread.isRunning():
            return
        text = self.link_input.toPlainText().strip()
        output_directory = self.folder_edit.text().strip()
        if not text:
            QMessageBox.warning(
                self, "Missing link", "Paste a TikTok or Douyin link first."
            )
            return
        if not output_directory:
            QMessageBox.warning(
                self, "Missing folder", "Choose a download folder first."
            )
            return

        self.settings.setValue("output_directory", output_directory)
        self.settings.sync()
        self._last_output_directory = output_directory
        self.open_folder_button.setEnabled(False)
        self.download_button.setEnabled(False)
        self.batch_progress.setValue(0)
        self.current_table.setRowCount(0)
        self._download_rows.clear()
        self._download_bars.clear()
        self.status_label.setText("Preparing download…")
        self.header_status.setText("Downloading")
        self.append_log("—" * 48)
        self.append_log(
            f"New download started: {datetime.now():%Y-%m-%d %H:%M:%S}"
        )

        worker = DownloadWorker(
            text=text,
            platform=str(self.platform_combo.currentData()),
            output_directory=output_directory,
            tiktok_cookie=self.settings.value("tiktok_cookie", "", str),
            douyin_cookie=self.settings.value("douyin_cookie", "", str),
            tiktok_proxy=self.settings.value("tiktok_proxy", "", str),
            douyin_proxy=self.settings.value("douyin_proxy", "", str),
        )
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self.batch_progress.setValue)
        worker.status.connect(self._set_status)
        worker.log.connect(self.append_log)
        worker.item_started.connect(self.on_item_started)
        worker.item_title.connect(self.on_item_title)
        worker.item_progress.connect(self.on_item_progress)
        worker.finished.connect(self.download_finished)
        worker.failed.connect(self.download_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self.thread_finished)
        self._worker = worker
        self._thread = thread
        thread.start()

    def _set_status(self, text: str) -> None:
        self.status_label.setText(text)
        self.header_status.setText(text)

    def on_item_started(
        self, index: int, total: int, url: str, platform: str
    ) -> None:
        row = self.current_table.rowCount()
        self.current_table.insertRow(row)
        self._download_rows[index] = row
        name = QTableWidgetItem(url)
        name.setToolTip(url)
        self.current_table.setItem(row, 0, name)
        self.current_table.setItem(row, 1, QTableWidgetItem(platform.title()))
        self.current_table.setItem(row, 2, QTableWidgetItem("Starting"))
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setTextVisible(False)
        self.current_table.setCellWidget(row, 3, bar)
        self._download_bars[index] = bar
        self.status_label.setText(f"Downloading {index} of {total}")

    def on_item_title(self, index: int, title: str) -> None:
        row = self._download_rows.get(index)
        if row is not None:
            self.current_table.setItem(row, 0, QTableWidgetItem(title))

    def on_item_progress(self, index: int, percent: int, status: str) -> None:
        row = self._download_rows.get(index)
        if row is not None:
            self.current_table.setItem(row, 2, QTableWidgetItem(status))
        bar = self._download_bars.get(index)
        if bar:
            bar.setValue(percent)

    def download_finished(self, result: dict) -> None:
        count = int(result.get("count", 0))
        self._last_output_directory = str(result.get("output_directory", ""))
        self.open_folder_button.setEnabled(bool(self._last_output_directory))
        self.status_label.setText(f"Completed · {count} item(s)")
        self.header_status.setText("Ready")
        self.append_log(f"Finished: {count} item(s) downloaded.")
        for item in result.get("results", []):
            self._add_history(
                title=str(item.get("title") or item.get("id") or "Downloaded item"),
                platform=str(item.get("platform") or ""),
                status="Completed",
                folder=self._last_output_directory,
            )
        self._refresh_home()
        QMessageBox.information(
            self,
            "Download complete",
            f"Downloaded {count} item(s).\n\nSaved to:\n{self._last_output_directory}",
        )

    def download_failed(self, message: str) -> None:
        self.status_label.setText("Download failed")
        self.header_status.setText("Failed")
        self.append_log(message)
        if self._download_rows:
            last_index = max(self._download_rows)
            row = self._download_rows[last_index]
            self.current_table.setItem(row, 2, QTableWidgetItem("Failed"))
        self._add_history(
            title="Download attempt",
            platform=str(self.platform_combo.currentText()),
            status="Failed",
            folder=self.folder_edit.text().strip(),
        )
        self._refresh_home()
        QMessageBox.critical(self, "Download failed", message)

    def thread_finished(self) -> None:
        self.download_button.setEnabled(True)
        self._thread = None
        self._worker = None

    def append_log(self, message: str) -> None:
        self.log_output.appendPlainText(message)

    def open_output_folder(self) -> None:
        if self._last_output_directory:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._last_output_directory))

    def _load_history(self) -> list[dict[str, str]]:
        raw = self.settings.value("history", "[]", str)
        try:
            data = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return []
        return data if isinstance(data, list) else []

    def _save_history(self) -> None:
        self.settings.setValue(
            "history", json.dumps(self.history[:100], ensure_ascii=False)
        )
        self.settings.sync()

    def _add_history(
        self, title: str, platform: str, status: str, folder: str
    ) -> None:
        self.history.insert(
            0,
            {
                "time": datetime.now().isoformat(timespec="seconds"),
                "title": title,
                "platform": platform.title(),
                "status": status,
                "folder": folder,
            },
        )
        self.history = self.history[:100]
        self._save_history()
        self._refresh_history_table()

    def _refresh_history_table(self) -> None:
        if not hasattr(self, "history_table"):
            return
        self.history_table.setRowCount(len(self.history))
        for row, item in enumerate(self.history):
            timestamp = str(item.get("time", "")).replace("T", " ")
            values = (
                timestamp,
                str(item.get("title", "")),
                str(item.get("platform", "")),
                str(item.get("status", "")),
                str(item.get("folder", "")),
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if column == 4:
                    cell.setToolTip(value)
                self.history_table.setItem(row, column, cell)

    def _refresh_home(self) -> None:
        today = datetime.now().date().isoformat()
        completed = [
            item for item in self.history if item.get("status") == "Completed"
        ]
        today_count = sum(
            1
            for item in completed
            if str(item.get("time", "")).startswith(today)
        )
        self.home_total.setText(str(len(completed)))
        self.home_today.setText(str(today_count))
        latest = self.history[0] if self.history else None
        self.home_last.setText(
            str(latest.get("status", "Ready")) if latest else "Ready"
        )
        if latest:
            self.home_recent.setText(
                f"{latest.get('time', '').replace('T', ' ')} · "
                f"{latest.get('status', '')} · {latest.get('title', '')}"
            )
        else:
            self.home_recent.setText("No downloads yet.")

    def open_selected_history_folder(self) -> None:
        row = self.history_table.currentRow()
        if row < 0 or row >= len(self.history):
            QMessageBox.information(self, "History", "Select a history row first.")
            return
        folder = str(self.history[row].get("folder", ""))
        if folder:
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def clear_history(self) -> None:
        answer = QMessageBox.question(
            self,
            "Clear history",
            "Remove all desktop download history? Downloaded files will not be deleted.",
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self._save_history()
            self._refresh_history_table()
            self._refresh_home()

    def _clipboard_toggled(self, enabled: bool) -> None:
        self.settings.setValue("clipboard_monitor", enabled)
        self.settings.sync()
        self._apply_clipboard_monitor_state()

    def _apply_clipboard_monitor_state(self) -> None:
        enabled = self.settings.value("clipboard_monitor", False, bool)
        if enabled:
            self.clipboard_timer.start()
        else:
            self.clipboard_timer.stop()

    def _check_clipboard(self) -> None:
        text = QApplication.clipboard().text().strip()
        if not text or text == self._last_clipboard:
            return
        lowered = text.lower()
        if (
            "tiktok.com" not in lowered
            and "douyin.com" not in lowered
            and "iesdouyin.com" not in lowered
        ):
            return
        self._last_clipboard = text
        self.clipboard_preview.setPlainText(text)
        self.header_status.setText("Link detected in clipboard")

    def send_clipboard_to_download(self) -> None:
        text = self.clipboard_preview.toPlainText().strip()
        if not text:
            text = QApplication.clipboard().text().strip()
        if text:
            self.link_input.setPlainText(text)
            self._navigate("download")

    def closeEvent(self, event) -> None:
        if self._thread and self._thread.isRunning():
            QMessageBox.information(
                self,
                "Download in progress",
                "Wait for the current download to finish before closing the app.",
            )
            event.ignore()
            return
        event.accept()
