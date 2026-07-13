from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QThread, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from .service import DownloadWorker


APP_STYLE = """
QMainWindow, QDialog {
    background: #0f172a;
}
QWidget {
    color: #e2e8f0;
    font-family: "Segoe UI";
    font-size: 14px;
}
QFrame#card {
    background: #111c33;
    border: 1px solid #26344f;
    border-radius: 14px;
}
QLabel#title {
    font-size: 28px;
    font-weight: 700;
    color: #f8fafc;
}
QLabel#subtitle, QLabel#hint {
    color: #94a3b8;
}
QPlainTextEdit, QLineEdit, QComboBox {
    background: #0b1324;
    border: 1px solid #334155;
    border-radius: 9px;
    padding: 9px;
    selection-background-color: #2563eb;
}
QPlainTextEdit:focus, QLineEdit:focus, QComboBox:focus {
    border: 1px solid #60a5fa;
}
QPushButton {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 9px;
    padding: 9px 14px;
    font-weight: 600;
}
QPushButton:hover {
    background: #273449;
}
QPushButton#primary {
    background: #2563eb;
    border-color: #3b82f6;
    color: white;
    padding: 11px 18px;
}
QPushButton#primary:hover {
    background: #1d4ed8;
}
QPushButton:disabled {
    background: #1e293b;
    color: #64748b;
}
QProgressBar {
    background: #0b1324;
    border: 1px solid #334155;
    border-radius: 7px;
    min-height: 13px;
    text-align: center;
}
QProgressBar::chunk {
    background: #3b82f6;
    border-radius: 6px;
}
"""


class SettingsDialog(QDialog):
    def __init__(self, settings: QSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Downloader settings")
        self.setMinimumWidth(620)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.tiktok_cookie = QPlainTextEdit()
        self.tiktok_cookie.setMaximumHeight(90)
        self.tiktok_cookie.setPlaceholderText("Optional TikTok Cookie")
        self.tiktok_cookie.setPlainText(settings.value("tiktok_cookie", "", str))

        self.douyin_cookie = QPlainTextEdit()
        self.douyin_cookie.setMaximumHeight(90)
        self.douyin_cookie.setPlaceholderText("Optional Douyin Cookie")
        self.douyin_cookie.setPlainText(settings.value("douyin_cookie", "", str))

        self.tiktok_proxy = QLineEdit(settings.value("tiktok_proxy", "", str))
        self.tiktok_proxy.setPlaceholderText("Example: http://127.0.0.1:7890")
        self.douyin_proxy = QLineEdit(settings.value("douyin_proxy", "", str))
        self.douyin_proxy.setPlaceholderText("Example: http://127.0.0.1:7890")

        form.addRow("TikTok Cookie", self.tiktok_cookie)
        form.addRow("Douyin Cookie", self.douyin_cookie)
        form.addRow("TikTok proxy", self.tiktok_proxy)
        form.addRow("Douyin proxy", self.douyin_proxy)
        layout.addLayout(form)

        warning = QLabel(
            "Cookies are saved locally through the operating-system settings store. "
            "Only use cookies from your own accounts."
        )
        warning.setObjectName("hint")
        warning.setWordWrap(True)
        layout.addWidget(warning)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self) -> None:
        self.settings.setValue("tiktok_cookie", self.tiktok_cookie.toPlainText().strip())
        self.settings.setValue("douyin_cookie", self.douyin_cookie.toPlainText().strip())
        self.settings.setValue("tiktok_proxy", self.tiktok_proxy.text().strip())
        self.settings.setValue("douyin_proxy", self.douyin_proxy.text().strip())
        self.settings.sync()
        super().accept()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings("WindyMaster", "DouKDownloaderDesktop")
        self._thread: QThread | None = None
        self._worker: DownloadWorker | None = None
        self._last_output_directory = ""

        self.setWindowTitle("DouK Downloader Desktop")
        self.resize(980, 720)
        self.setMinimumSize(780, 620)
        self.setStyleSheet(APP_STYLE)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(30, 24, 30, 26)
        root.setSpacing(18)
        self.setCentralWidget(central)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel("DouK Downloader")
        title.setObjectName("title")
        subtitle = QLabel("Download TikTok and Douyin videos or photo posts")
        subtitle.setObjectName("subtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addLayout(titles)
        header.addSpacerItem(
            QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.open_settings)
        header.addWidget(self.settings_button)
        root.addLayout(header)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 22, 22, 22)
        card_layout.setSpacing(14)

        link_label = QLabel("Video or photo-post links")
        link_label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        card_layout.addWidget(link_label)

        self.link_input = QPlainTextEdit()
        self.link_input.setPlaceholderText(
            "Paste one or more TikTok/Douyin share links here…\n"
            "You can paste the complete share message too."
        )
        self.link_input.setMinimumHeight(135)
        card_layout.addWidget(self.link_input)

        options = QHBoxLayout()
        self.platform_combo = QComboBox()
        self.platform_combo.addItem("Auto detect", "auto")
        self.platform_combo.addItem("TikTok", "tiktok")
        self.platform_combo.addItem("Douyin", "douyin")
        options.addWidget(QLabel("Platform"))
        options.addWidget(self.platform_combo, 1)
        options.addSpacing(12)

        self.folder_edit = QLineEdit()
        default_folder = str(Path.home() / "Downloads" / "DouK-Downloader")
        self.folder_edit.setText(self.settings.value("output_directory", default_folder, str))
        self.folder_edit.setPlaceholderText("Choose download folder")
        options.addWidget(QLabel("Save to"))
        options.addWidget(self.folder_edit, 3)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.choose_folder)
        options.addWidget(browse_button)
        card_layout.addLayout(options)

        action_row = QHBoxLayout()
        paste_button = QPushButton("Paste clipboard")
        paste_button.clicked.connect(self.paste_clipboard)
        action_row.addWidget(paste_button)
        action_row.addStretch(1)

        self.download_button = QPushButton("Download")
        self.download_button.setObjectName("primary")
        self.download_button.clicked.connect(self.start_download)
        action_row.addWidget(self.download_button)
        card_layout.addLayout(action_row)
        root.addWidget(card)

        status_card = QFrame()
        status_card.setObjectName("card")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(22, 18, 22, 20)
        status_layout.setSpacing(11)

        status_header = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        status_header.addWidget(self.status_label)
        status_header.addStretch(1)

        self.open_folder_button = QPushButton("Open folder")
        self.open_folder_button.setEnabled(False)
        self.open_folder_button.clicked.connect(self.open_output_folder)
        status_header.addWidget(self.open_folder_button)
        status_layout.addLayout(status_header)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        status_layout.addWidget(self.progress)

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Download activity will appear here.")
        status_layout.addWidget(self.log_output, 1)
        root.addWidget(status_card, 1)

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

    def open_settings(self) -> None:
        SettingsDialog(self.settings, self).exec()

    def start_download(self) -> None:
        if self._thread and self._thread.isRunning():
            return

        text = self.link_input.toPlainText().strip()
        output_directory = self.folder_edit.text().strip()
        if not text:
            QMessageBox.warning(self, "Missing link", "Paste a TikTok or Douyin link first.")
            return
        if not output_directory:
            QMessageBox.warning(self, "Missing folder", "Choose a download folder first.")
            return

        self.settings.setValue("output_directory", output_directory)
        self.settings.sync()
        self._last_output_directory = output_directory
        self.open_folder_button.setEnabled(False)
        self.download_button.setEnabled(False)
        self.settings_button.setEnabled(False)
        self.progress.setValue(0)
        self.log_output.clear()
        self.status_label.setText("Preparing download…")

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
        worker.progress.connect(self.progress.setValue)
        worker.status.connect(self.status_label.setText)
        worker.log.connect(self.append_log)
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

    def append_log(self, message: str) -> None:
        self.log_output.appendPlainText(message)

    def download_finished(self, result: dict) -> None:
        count = int(result.get("count", 0))
        self._last_output_directory = str(result.get("output_directory", ""))
        self.append_log(f"Finished: {count} item(s) downloaded.")
        self.open_folder_button.setEnabled(bool(self._last_output_directory))
        QMessageBox.information(
            self,
            "Download complete",
            f"Downloaded {count} item(s).\n\nSaved to:\n{self._last_output_directory}",
        )

    def download_failed(self, message: str) -> None:
        self.status_label.setText("Download failed")
        self.append_log(message)
        QMessageBox.critical(self, "Download failed", message)

    def thread_finished(self) -> None:
        self.download_button.setEnabled(True)
        self.settings_button.setEnabled(True)
        self._thread = None
        self._worker = None

    def open_output_folder(self) -> None:
        if self._last_output_directory:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._last_output_directory))

    def closeEvent(self, event) -> None:
        if self._thread and self._thread.isRunning():
            QMessageBox.information(
                self,
                "Download running",
                "Please let the current download finish before closing the app.",
            )
            event.ignore()
            return
        event.accept()
