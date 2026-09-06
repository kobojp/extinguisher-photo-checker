import sys
from pathlib import Path
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from ui import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(Path(__file__).resolve().parent / 'assets' / 'app-icon.ico')))
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
