from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from src.desktop import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("DouK Downloader Desktop")
    app.setOrganizationName("WindyMaster")

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
