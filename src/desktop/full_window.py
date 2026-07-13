from __future__ import annotations

from collections import deque
from pathlib import Path

from PySide6.QtCore import QThread, QTimer, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .advanced_service import BatchSourceWorker
from .enhanced_window import MainWindow as EngineMainWindow


COOKIE_GUIDE_URL = (
    "https://github.com/JoeanAmier/TikTokDownloader/blob/master/"
    "docs/Cookie%E8%8E%B7%E5%8F%96%E6%95%99%E7%A8%8B.md"
)


class MainWindow(EngineMainWindow):
    """Desktop milestone 4: native account/collection tools and accurate guidance."""

    def __init__(self) -> None:
        self._advanced_thread: QThread | None = None
        self._advanced_worker: BatchSourceWorker | None = None
        self._advanced_kind = ""
        self._clipboard_queue: deque[str] = deque()
        super().__init__()

        self._replace_advanced_pages()
        self._install_feature_guide()
        self._upgrade_clipboard_page()
        self._upgrade_tools_page()

    def _replace_page(self, key: str, page: QWidget) -> None:
        old_page = self.pages[key]
        index = self.stack.indexOf(old_page)
        self.stack.removeWidget(old_page)
        self.stack.insertWidget(index, page)
        self.pages[key] = page
        old_page.deleteLater()

    def _replace_advanced_pages(self) -> None:
        self._replace_page("accounts", self._build_accounts_page())
        self._replace_page("collections", self._build_collections_page())
        self._replace_page("live", self._build_live_page())

    def _install_feature_guide(self) -> None:
        self.guide_page = self._build_feature_guide_page()
        self.pages["guide"] = self.guide_page
        self.stack.addWidget(self.guide_page)

        sidebar = self.findChild(QFrame, "sidebar")
        if sidebar is None or sidebar.layout() is None:
            return

        button = QPushButton("?  Feature Guide")
        button.setObjectName("navButton")
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda checked=False: self._navigate("guide"))
        self.nav_group.addButton(button)
        self.nav_buttons["guide"] = button

        layout = sidebar.layout()
        tools_button = self.nav_buttons.get("tools")
        index = layout.indexOf(tools_button) if tools_button else max(0, layout.count() - 2)
        layout.insertWidget(max(0, index), button)

    def _navigate(self, key: str) -> None:
        if key == "guide":
            self.stack.setCurrentWidget(self.guide_page)
            self.nav_buttons["guide"].setChecked(True)
            self.page_title.setText("Feature Guide")
            self.page_subtitle.setText(
                "What every original terminal option does and how to use it"
            )
            return
        super()._navigate(key)

    def _build_accounts_page(self) -> QWidget:
        page, layout = self._page_container()

        info, info_layout = self._card()
        title = QLabel("Batch Download Account Posts")
        title.setObjectName("sectionTitle")
        info_layout.addWidget(title)
        note = QLabel(
            "Paste one or more public TikTok or Douyin profile links. This desktop "
            "page uses yt-dlp and does not require you to edit accounts_urls_tiktok "
            "inside settings.json."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        info_layout.addWidget(note)
        warning = QLabel(
            "Why the terminal showed 0 accounts: you selected source option 1, which "
            "only reads profiles already stored in settings.json. For a one-time link "
            "in the terminal, choose source option 2 instead."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet(
            "background:#172554; color:#bfdbfe; border:1px solid #1d4ed8; "
            "border-radius:8px; padding:10px;"
        )
        info_layout.addWidget(warning)
        layout.addWidget(info)

        form, form_layout = self._card()
        self.account_input = QPlainTextEdit()
        self.account_input.setPlaceholderText(
            "Examples:\nhttps://www.tiktok.com/@username\n"
            "https://www.douyin.com/user/..."
        )
        self.account_input.setMinimumHeight(95)
        form_layout.addWidget(self.account_input)

        options = QGridLayout()
        options.setHorizontalSpacing(10)
        options.setVerticalSpacing(10)

        options.addWidget(QLabel("Platform"), 0, 0)
        self.account_platform = QComboBox()
        self.account_platform.addItem("Auto detect", "auto")
        self.account_platform.addItem("TikTok", "tiktok")
        self.account_platform.addItem("Douyin", "douyin")
        options.addWidget(self.account_platform, 0, 1)

        options.addWidget(QLabel("Maximum posts per profile"), 0, 2)
        self.account_limit = QSpinBox()
        self.account_limit.setRange(1, 500)
        self.account_limit.setValue(
            self.settings.value("account_max_items", 20, int)
        )
        options.addWidget(self.account_limit, 0, 3)

        options.addWidget(QLabel("Save to"), 1, 0)
        self.account_folder = QLineEdit(
            self.settings.value(
                "account_output_directory",
                str(Path.home() / "Downloads" / "TikTok-Downloader" / "Accounts"),
                str,
            )
        )
        options.addWidget(self.account_folder, 1, 1, 1, 2)
        browse = QPushButton("Browse")
        browse.clicked.connect(lambda: self._choose_target(self.account_folder))
        options.addWidget(browse, 1, 3)
        form_layout.addLayout(options)

        actions = QHBoxLayout()
        paste = QPushButton("Paste Clipboard")
        paste.clicked.connect(lambda: self._paste_into(self.account_input))
        actions.addWidget(paste)
        actions.addStretch(1)
        self.account_download_button = QPushButton("Download Account")
        self.account_download_button.setObjectName("primary")
        self.account_download_button.clicked.connect(
            lambda: self._start_advanced_download("account")
        )
        actions.addWidget(self.account_download_button)
        form_layout.addLayout(actions)
        layout.addWidget(form)

        status_card, status_layout = self._card()
        status_row = QHBoxLayout()
        status_title = QLabel("Account Download Activity")
        status_title.setObjectName("sectionTitle")
        status_row.addWidget(status_title)
        status_row.addStretch(1)
        self.account_status = QLabel("Ready")
        self.account_status.setObjectName("muted")
        status_row.addWidget(self.account_status)
        open_folder = QPushButton("Open Folder")
        open_folder.clicked.connect(lambda: self._open_path(self.account_folder.text()))
        status_row.addWidget(open_folder)
        status_layout.addLayout(status_row)

        self.account_progress = QProgressBar()
        self.account_progress.setRange(0, 100)
        self.account_progress.setTextVisible(False)
        status_layout.addWidget(self.account_progress)

        self.account_log = QPlainTextEdit()
        self.account_log.setReadOnly(True)
        self.account_log.setPlaceholderText("Account-download activity appears here.")
        status_layout.addWidget(self.account_log)
        layout.addWidget(status_card, 1)
        return page

    def _build_collections_page(self) -> QWidget:
        page, layout = self._page_container()

        info, info_layout = self._card()
        title = QLabel("Download Collections / Playlists")
        title.setObjectName("sectionTitle")
        info_layout.addWidget(title)
        note = QLabel(
            "Paste TikTok playlist/collection links or supported Douyin collection "
            "links. The downloader saves each collection inside its own folder."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        info_layout.addWidget(note)
        layout.addWidget(info)

        form, form_layout = self._card()
        self.collection_input = QPlainTextEdit()
        self.collection_input.setPlaceholderText(
            "Paste one or more collection or playlist links here."
        )
        self.collection_input.setMinimumHeight(95)
        form_layout.addWidget(self.collection_input)

        options = QGridLayout()
        options.setHorizontalSpacing(10)
        options.setVerticalSpacing(10)

        options.addWidget(QLabel("Platform"), 0, 0)
        self.collection_platform = QComboBox()
        self.collection_platform.addItem("Auto detect", "auto")
        self.collection_platform.addItem("TikTok", "tiktok")
        self.collection_platform.addItem("Douyin", "douyin")
        options.addWidget(self.collection_platform, 0, 1)

        options.addWidget(QLabel("Maximum items per link"), 0, 2)
        self.collection_limit = QSpinBox()
        self.collection_limit.setRange(1, 1000)
        self.collection_limit.setValue(
            self.settings.value("collection_max_items", 50, int)
        )
        options.addWidget(self.collection_limit, 0, 3)

        options.addWidget(QLabel("Save to"), 1, 0)
        self.collection_folder = QLineEdit(
            self.settings.value(
                "collection_output_directory",
                str(Path.home() / "Downloads" / "TikTok-Downloader" / "Collections"),
                str,
            )
        )
        options.addWidget(self.collection_folder, 1, 1, 1, 2)
        browse = QPushButton("Browse")
        browse.clicked.connect(lambda: self._choose_target(self.collection_folder))
        options.addWidget(browse, 1, 3)
        form_layout.addLayout(options)

        actions = QHBoxLayout()
        paste = QPushButton("Paste Clipboard")
        paste.clicked.connect(lambda: self._paste_into(self.collection_input))
        actions.addWidget(paste)
        actions.addStretch(1)
        self.collection_download_button = QPushButton("Download Collection")
        self.collection_download_button.setObjectName("primary")
        self.collection_download_button.clicked.connect(
            lambda: self._start_advanced_download("collection")
        )
        actions.addWidget(self.collection_download_button)
        form_layout.addLayout(actions)
        layout.addWidget(form)

        status_card, status_layout = self._card()
        status_row = QHBoxLayout()
        status_title = QLabel("Collection Download Activity")
        status_title.setObjectName("sectionTitle")
        status_row.addWidget(status_title)
        status_row.addStretch(1)
        self.collection_status = QLabel("Ready")
        self.collection_status.setObjectName("muted")
        status_row.addWidget(self.collection_status)
        open_folder = QPushButton("Open Folder")
        open_folder.clicked.connect(
            lambda: self._open_path(self.collection_folder.text())
        )
        status_row.addWidget(open_folder)
        status_layout.addLayout(status_row)

        self.collection_progress = QProgressBar()
        self.collection_progress.setRange(0, 100)
        self.collection_progress.setTextVisible(False)
        status_layout.addWidget(self.collection_progress)

        self.collection_log = QPlainTextEdit()
        self.collection_log.setReadOnly(True)
        self.collection_log.setPlaceholderText(
            "Collection-download activity appears here."
        )
        status_layout.addWidget(self.collection_log)
        layout.addWidget(status_card, 1)
        return page

    def _build_live_page(self) -> QWidget:
        page, layout = self._page_container()

        overview, overview_layout = self._card()
        title = QLabel("Live Stream Tools")
        title.setObjectName("sectionTitle")
        overview_layout.addWidget(title)
        note = QLabel(
            "The original terminal's live options resolve a live-stream pull URL. "
            "Recording an ongoing stream also needs FFmpeg and a reliable Stop control, "
            "so native desktop recording remains disabled until that safety control is added."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        overview_layout.addWidget(note)
        layout.addWidget(overview)

        steps, steps_layout = self._card()
        steps_title = QLabel("Use the Original Live Tool")
        steps_title.setObjectName("sectionTitle")
        steps_layout.addWidget(steps_title)
        instructions = QLabel(
            "1. Open the original terminal.\n"
            "2. Select 5 — Terminal Mode.\n"
            "3. Select 3 for Douyin live or 15 for TikTok live.\n"
            "4. Paste the live-room URL.\n\n"
            "A valid platform cookie may be required. The tool returns the stream URL; "
            "it is not the same as the Web API documentation page."
        )
        instructions.setWordWrap(True)
        steps_layout.addWidget(instructions)

        buttons = QHBoxLayout()
        terminal = QPushButton("Open Original Terminal")
        terminal.setObjectName("primary")
        terminal.clicked.connect(self.open_terminal_mode)
        buttons.addWidget(terminal)
        settings = QPushButton("Open Cookie Settings")
        settings.clicked.connect(lambda: self._navigate("settings"))
        buttons.addWidget(settings)
        docs = QPushButton("Open API Docs")
        docs.clicked.connect(self.open_api_docs)
        buttons.addWidget(docs)
        buttons.addStretch(1)
        steps_layout.addLayout(buttons)
        layout.addWidget(steps)
        layout.addStretch(1)
        return page

    def _build_feature_guide_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 26)
        layout.setSpacing(16)

        cookie, cookie_layout = self._card()
        title = QLabel("Cookie Setup — Terminal Options 1 to 4")
        title.setObjectName("sectionTitle")
        cookie_layout.addWidget(title)
        explanation = QLabel(
            "Options 1 and 3 let you paste/type a Cookie directly. Options 2 and 4 "
            "read the Cookie already copied to the Windows clipboard. The only platform "
            "difference is Douyin versus TikTok."
        )
        explanation.setWordWrap(True)
        cookie_layout.addWidget(explanation)

        steps = QLabel(
            "Simple method:\n"
            "1. Log in to TikTok or Douyin in Edge/Chrome.\n"
            "2. Press F12 → Network, then reload the page.\n"
            "3. Open a request made to the same platform.\n"
            "4. Under Request Headers, copy the complete Cookie value.\n"
            "5. Return here → Settings, paste it into the matching Cookie box, and save.\n\n"
            "For Douyin, the upstream guide suggests filtering Network requests with "
            "cookie-name:odin_tt and opening a video comment section."
        )
        steps.setObjectName("muted")
        steps.setWordWrap(True)
        cookie_layout.addWidget(steps)

        cookie_buttons = QHBoxLayout()
        open_tiktok = QPushButton("Open TikTok")
        open_tiktok.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://www.tiktok.com/"))
        )
        cookie_buttons.addWidget(open_tiktok)
        open_douyin = QPushButton("Open Douyin")
        open_douyin.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://www.douyin.com/"))
        )
        cookie_buttons.addWidget(open_douyin)
        upstream = QPushButton("Open Original Cookie Guide")
        upstream.clicked.connect(self.open_cookie_guide)
        cookie_buttons.addWidget(upstream)
        settings = QPushButton("Open Desktop Settings")
        settings.setObjectName("primary")
        settings.clicked.connect(lambda: self._navigate("settings"))
        cookie_buttons.addWidget(settings)
        cookie_buttons.addStretch(1)
        cookie_layout.addLayout(cookie_buttons)
        layout.addWidget(cookie)

        terminal, terminal_layout = self._card()
        terminal_title = QLabel("Terminal Modes — Options 5 to 8")
        terminal_title.setObjectName("sectionTitle")
        terminal_layout.addWidget(terminal_title)
        terminal_layout.addWidget(
            self._feature_line(
                "5 · Terminal Mode",
                "The full 15-item feature menu: account posts, links, live URLs, "
                "comments, collections, account details, search, hot board, favorites, "
                "favorite music, and favorite folders.",
            )
        )
        terminal_layout.addWidget(
            self._feature_line(
                "6 · Monitoring Mode",
                "Continuously watches the clipboard. When it sees a TikTok or Douyin "
                "link, it automatically downloads it. Stop with Ctrl+C or copy the word close.",
            )
        )
        terminal_layout.addWidget(
            self._feature_line(
                "7 · Web API Mode",
                "Starts a local developer API on port 5555. /docs is Swagger and /redoc "
                "is ReDoc. These are API testing pages, not a normal downloader Web UI.",
            )
        )
        terminal_layout.addWidget(
            self._feature_line(
                "8 · Web UI Mode",
                "Disabled in the upstream project while it is being rebuilt. There is "
                "nothing wrong with your computer; that option is intentionally unavailable.",
            )
        )
        terminal_buttons = QHBoxLayout()
        open_terminal = QPushButton("Open Original Terminal")
        open_terminal.setObjectName("primary")
        open_terminal.clicked.connect(self.open_terminal_mode)
        terminal_buttons.addWidget(open_terminal)
        monitor = QPushButton("Enable Auto Clipboard Download")
        monitor.clicked.connect(self.open_monitoring_mode)
        terminal_buttons.addWidget(monitor)
        api = QPushButton("Open Engine Tools")
        api.clicked.connect(lambda: self._navigate("tools"))
        terminal_buttons.addWidget(api)
        terminal_buttons.addStretch(1)
        terminal_layout.addLayout(terminal_buttons)
        layout.addWidget(terminal)

        maintenance, maintenance_layout = self._card()
        maintenance_title = QLabel("History, Logs, Updates, Language — Options 9 to 13")
        maintenance_title.setObjectName("sectionTitle")
        maintenance_layout.addWidget(maintenance_title)
        maintenance_layout.addWidget(
            self._feature_line(
                "9 · Works Download History",
                "Toggles the original engine's downloaded-ID database. When enabled, "
                "already recorded works can be skipped on later runs.",
            )
        )
        maintenance_layout.addWidget(
            self._feature_line(
                "10 · Delete Works Download History",
                "Clears only the original engine's recorded work IDs. It does not delete media files.",
            )
        )
        maintenance_layout.addWidget(
            self._feature_line(
                "11 · Run Log History",
                "Toggles detailed runtime log files for the original engine.",
            )
        )
        maintenance_layout.addWidget(
            self._feature_line(
                "12 · Check for Updates",
                "Checks the upstream project's latest release.",
            )
        )
        maintenance_layout.addWidget(
            self._feature_line(
                "13 · Language",
                "Switches the original terminal between English and Simplified Chinese.",
            )
        )
        maintenance_button = QPushButton("Manage These in Engine Tools")
        maintenance_button.setObjectName("primary")
        maintenance_button.clicked.connect(lambda: self._navigate("tools"))
        maintenance_layout.addWidget(
            maintenance_button, 0, Qt.AlignmentFlag.AlignLeft
        )
        layout.addWidget(maintenance)

        account, account_layout = self._card()
        account_title = QLabel("Why Your TikTok Account Test Downloaded 0 Items")
        account_title.setObjectName("sectionTitle")
        account_layout.addWidget(account_title)
        reason = QLabel(
            "You selected Terminal Mode → 12 (TikTok account posts) → source 1. "
            "Source 1 means: read the accounts_urls_tiktok list from settings.json. "
            "That list currently contains no enabled profile URL, so the program correctly "
            "reported 0 accounts. Choose source 2 and paste a profile URL, or use the new "
            "Accounts page in this desktop app."
        )
        reason.setWordWrap(True)
        account_layout.addWidget(reason)
        account_button = QPushButton("Open Accounts Page")
        account_button.setObjectName("primary")
        account_button.clicked.connect(lambda: self._navigate("accounts"))
        account_layout.addWidget(account_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(account)

        layout.addStretch(1)
        scroll.setWidget(content)
        outer.addWidget(scroll)
        return page

    @staticmethod
    def _feature_line(title: str, description: str) -> QLabel:
        label = QLabel(f"<b>{title}</b><br>{description}")
        label.setWordWrap(True)
        label.setStyleSheet(
            "background:#0c1628; border:1px solid #24324a; "
            "border-radius:8px; padding:10px;"
        )
        return label

    def open_cookie_guide(self) -> None:
        QDesktopServices.openUrl(QUrl(COOKIE_GUIDE_URL))

    def _upgrade_clipboard_page(self) -> None:
        layout = self.pages["clipboard"].layout()
        if layout is None:
            return

        card, card_layout = self._card()
        title = QLabel("Automatic Download Mode")
        title.setObjectName("sectionTitle")
        card_layout.addWidget(title)
        note = QLabel(
            "This matches original terminal option 6: when a supported link is copied, "
            "the desktop app sends it to the Download page automatically. Links copied "
            "while another download is running wait in a small queue."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        card_layout.addWidget(note)

        self.auto_clipboard_download = QCheckBox(
            "Automatically download detected clipboard links"
        )
        self.auto_clipboard_download.setChecked(
            self.settings.value("clipboard_auto_download", False, bool)
        )
        self.auto_clipboard_download.toggled.connect(
            self._auto_clipboard_toggled
        )
        card_layout.addWidget(self.auto_clipboard_download)

        self.clipboard_queue_label = QLabel("Queue: 0 link(s)")
        self.clipboard_queue_label.setObjectName("muted")
        card_layout.addWidget(self.clipboard_queue_label)

        layout.insertWidget(max(0, layout.count() - 1), card)

    def _auto_clipboard_toggled(self, enabled: bool) -> None:
        self.settings.setValue("clipboard_auto_download", enabled)
        if enabled:
            self.clipboard_toggle.setChecked(True)
        self.settings.sync()

    def open_monitoring_mode(self) -> None:
        self.clipboard_toggle.setChecked(True)
        self.auto_clipboard_download.setChecked(True)
        self._navigate("clipboard")
        self.header_status.setText("Automatic clipboard downloads enabled")

    def _check_clipboard(self) -> None:
        previous = self._last_clipboard
        super()._check_clipboard()
        if (
            self._last_clipboard
            and self._last_clipboard != previous
            and hasattr(self, "auto_clipboard_download")
            and self.auto_clipboard_download.isChecked()
        ):
            self._queue_or_download_clipboard(self._last_clipboard)

    def _queue_or_download_clipboard(self, text: str) -> None:
        busy = bool(
            (self._thread and self._thread.isRunning())
            or (self._advanced_thread and self._advanced_thread.isRunning())
        )
        if busy:
            if text not in self._clipboard_queue:
                self._clipboard_queue.append(text)
                self.append_log("Clipboard link queued for automatic download.")
                self._refresh_clipboard_queue_label()
            return

        self.link_input.setPlainText(text)
        self._navigate("download")
        QTimer.singleShot(150, self.start_download)

    def _process_clipboard_queue(self) -> None:
        if (
            self._clipboard_queue
            and not (self._thread and self._thread.isRunning())
            and not (self._advanced_thread and self._advanced_thread.isRunning())
        ):
            text = self._clipboard_queue.popleft()
            self._refresh_clipboard_queue_label()
            self.link_input.setPlainText(text)
            self._navigate("download")
            QTimer.singleShot(150, self.start_download)

    def _refresh_clipboard_queue_label(self) -> None:
        if hasattr(self, "clipboard_queue_label"):
            self.clipboard_queue_label.setText(
                f"Queue: {len(self._clipboard_queue)} link(s)"
            )

    def thread_finished(self) -> None:
        super().thread_finished()
        QTimer.singleShot(200, self._process_clipboard_queue)

    def _upgrade_tools_page(self) -> None:
        layout = self.tools_page.layout()
        if layout is None:
            return
        card, card_layout = self._card()
        title = QLabel("Important Clarification")
        title.setObjectName("sectionTitle")
        card_layout.addWidget(title)
        note = QLabel(
            "Web API Mode (option 7) opens Swagger/ReDoc developer documentation. "
            "It is not the old Web UI. Web UI Mode (option 8) is disabled upstream. "
            "Use Feature Guide for a plain-English explanation of every option."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        card_layout.addWidget(note)
        guide = QPushButton("Open Feature Guide")
        guide.setObjectName("primary")
        guide.clicked.connect(lambda: self._navigate("guide"))
        card_layout.addWidget(guide, 0, Qt.AlignmentFlag.AlignLeft)
        layout.insertWidget(1, card)

    def _start_advanced_download(self, kind: str) -> None:
        if (self._thread and self._thread.isRunning()) or (
            self._advanced_thread and self._advanced_thread.isRunning()
        ):
            QMessageBox.information(
                self,
                "Downloader busy",
                "Wait for the current download to finish before starting another.",
            )
            return

        if kind == "account":
            text = self.account_input.toPlainText().strip()
            platform = str(self.account_platform.currentData())
            folder = self.account_folder.text().strip()
            maximum = self.account_limit.value()
            progress = self.account_progress
            status = self.account_status
            log = self.account_log
            button = self.account_download_button
            setting_prefix = "account"
        else:
            text = self.collection_input.toPlainText().strip()
            platform = str(self.collection_platform.currentData())
            folder = self.collection_folder.text().strip()
            maximum = self.collection_limit.value()
            progress = self.collection_progress
            status = self.collection_status
            log = self.collection_log
            button = self.collection_download_button
            setting_prefix = "collection"

        if not text:
            QMessageBox.warning(
                self,
                "Missing link",
                "Paste at least one complete profile or collection link.",
            )
            return
        if not folder:
            QMessageBox.warning(self, "Missing folder", "Choose a save folder first.")
            return

        self.settings.setValue(f"{setting_prefix}_output_directory", folder)
        self.settings.setValue(f"{setting_prefix}_max_items", maximum)
        self.settings.sync()

        progress.setValue(0)
        status.setText("Preparing…")
        log.clear()
        button.setEnabled(False)
        self.header_status.setText("Downloading")
        self._advanced_kind = kind

        worker = BatchSourceWorker(
            text=text,
            source_kind=kind,
            platform=platform,
            output_directory=folder,
            max_items=maximum,
            tiktok_cookie=self.settings.value("tiktok_cookie", "", str),
            douyin_cookie=self.settings.value("douyin_cookie", "", str),
            tiktok_proxy=self.settings.value("tiktok_proxy", "", str),
            douyin_proxy=self.settings.value("douyin_proxy", "", str),
        )
        thread = QThread(self)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.progress.connect(progress.setValue)
        worker.status.connect(status.setText)
        worker.status.connect(self.header_status.setText)
        worker.log.connect(log.appendPlainText)
        worker.log.connect(self.append_log)
        worker.finished.connect(self._advanced_finished)
        worker.failed.connect(self._advanced_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._advanced_thread_finished)

        self._advanced_worker = worker
        self._advanced_thread = thread
        thread.start()

    def _advanced_finished(self, result: dict) -> None:
        count = int(result.get("count", 0))
        folder = str(result.get("output_directory", ""))
        kind = str(result.get("kind", self._advanced_kind)).title()
        self._last_output_directory = folder
        self.header_status.setText("Ready")

        for item in result.get("results", []):
            self._add_history(
                title=str(item.get("title") or item.get("id") or f"{kind} item"),
                platform=str(item.get("platform") or ""),
                status="Completed",
                folder=folder,
            )
        self._refresh_home()

        QMessageBox.information(
            self,
            f"{kind} download complete",
            f"Downloaded {count} item(s).\n\nSaved to:\n{folder}",
        )

    def _advanced_failed(self, message: str) -> None:
        if self._advanced_kind == "account":
            self.account_status.setText("Failed")
            self.account_log.appendPlainText(message)
        else:
            self.collection_status.setText("Failed")
            self.collection_log.appendPlainText(message)
        self.header_status.setText("Failed")
        self.append_log(message)
        QMessageBox.critical(self, "Download failed", message)

    def _advanced_thread_finished(self) -> None:
        self.account_download_button.setEnabled(True)
        self.collection_download_button.setEnabled(True)
        self._advanced_worker = None
        self._advanced_thread = None
        self._advanced_kind = ""
        QTimer.singleShot(200, self._process_clipboard_queue)

    def _choose_target(self, field: QLineEdit) -> None:
        selected = QFileDialog.getExistingDirectory(
            self, "Choose download folder", field.text() or str(Path.home())
        )
        if selected:
            field.setText(selected)

    @staticmethod
    def _paste_into(editor: QPlainTextEdit) -> None:
        text = QApplication.clipboard().text().strip()
        if text:
            current = editor.toPlainText().strip()
            editor.setPlainText(f"{current}\n{text}".strip())

    @staticmethod
    def _open_path(path: str) -> None:
        if path:
            Path(path).expanduser().mkdir(parents=True, exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(path).expanduser())))

    def closeEvent(self, event) -> None:
        if self._advanced_thread and self._advanced_thread.isRunning():
            QMessageBox.information(
                self,
                "Download in progress",
                "Wait for the account or collection download to finish before closing.",
            )
            event.ignore()
            return
        super().closeEvent(event)
