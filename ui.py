from pathlib import Path
from PySide6.QtCore import QSettings, QThread, Signal, QUrl
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton,
    QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)
from checker import READY, ERROR, check_folders, export_csv, parse_codes

DEFAULT_ROOT = r'I:\.shortcut-targets-by-id\1Igs5p6nQ7Yr9eYKh_C9ADd8ghn1__kIo\桃隆消防\滅火器更換照片\2026年\滅火器\2026年'


class Worker(QThread):
    completed = Signal(object)

    def __init__(self, path, codes):
        super().__init__()
        self.path, self.codes = path, codes

    def run(self):
        try:
            self.completed.emit(check_folders(self.path, self.codes))
        except Exception as exc:
            self.completed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('滅火器照片核對')
        self.resize(1120, 740)
        self.settings = QSettings('Taolong', 'ExtinguisherPhotoChecker')
        self.results, self.worker = [], None
        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel('滅火器照片核對')
        title.setStyleSheet('font-size: 26px; font-weight: bold;')
        layout.addWidget(title)
        layout.addWidget(QLabel('選擇月份、貼上編號，快速找出需要補照片的資料夾。'))
        row = QHBoxLayout()
        row.addWidget(QLabel('年度根目錄'))
        self.root = QLineEdit(self.settings.value('root', DEFAULT_ROOT))
        row.addWidget(self.root, 1)
        self.browse = QPushButton('選擇資料夾')
        self.browse.clicked.connect(self.choose_root)
        row.addWidget(self.browse)
        layout.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(QLabel('月份資料夾'))
        self.month = QComboBox()
        row.addWidget(self.month, 1)
        self.refresh = QPushButton('重新讀取月份')
        self.refresh.clicked.connect(self.load_months)
        row.addWidget(self.refresh)
        self.start = QPushButton('開始核對')
        self.start.setStyleSheet('background: #176b53; color: white; font-weight: bold; padding: 10px 24px;')
        self.start.clicked.connect(self.run_check)
        row.addWidget(self.start)
        layout.addLayout(row)
        split = QSplitter()
        left, right = QWidget(), QWidget()
        ll, rl = QVBoxLayout(left), QVBoxLayout(right)
        ll.addWidget(QLabel('核對編號 · 支援 Excel 與 Markdown 表格'))
        input_actions = QHBoxLayout()
        input_actions.addStretch()
        self.clear_input = QPushButton('清除')
        self.clear_input.setToolTip('清除左側全部核對編號')
        input_actions.addWidget(self.clear_input)
        ll.addLayout(input_actions)
        self.input = QPlainTextEdit()
        self.clear_input.clicked.connect(self.input.clear)
        self.input.setPlaceholderText('每行貼上一個編號，例如：\n中-01-122\n中-01-123')
        ll.addWidget(self.input)
        self.input_info = QLabel('尚未輸入編號')
        self.input_info.setWordWrap(True)
        ll.addWidget(self.input_info)
        self.input.textChanged.connect(self.update_input)
        self.summary = QLabel('尚未核對')
        self.summary.setWordWrap(True)
        rl.addWidget(self.summary)
        self.filter = QComboBox()
        self.filter.addItems(['待補資料', '全部', '已有照片'])
        self.filter.currentIndexChanged.connect(self.render_results)
        rl.addWidget(self.filter)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(['編號', '狀態', '照片數', '資料夾／說明'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.cellDoubleClicked.connect(self.open_folder)
        rl.addWidget(self.table)
        rl.addWidget(QLabel('點兩下結果開啟資料夾；同編號有多個資料夾時可選擇。'))
        split.addWidget(left)
        split.addWidget(right)
        split.setSizes([320, 740])
        layout.addWidget(split, 1)
        row = QHBoxLayout()
        self.status = QLabel('只讀取檔名及檔案大小，不更動照片。')
        row.addWidget(self.status, 1)
        self.copy = QPushButton('複製待補清單')
        self.copy.clicked.connect(self.copy_missing)
        row.addWidget(self.copy)
        self.export = QPushButton('匯出全部 CSV')
        self.export.clicked.connect(self.save_csv)
        row.addWidget(self.export)
        layout.addLayout(row)
        self.setStyleSheet('QWidget { font-family: "Microsoft JhengHei UI"; font-size: 14px; } QLineEdit, QComboBox, QPushButton { min-height: 30px; } QTableWidget { alternate-background-color: #f1f5f4; }')
        self.table.setAlternatingRowColors(True)
        self.root.editingFinished.connect(self.load_months)
        self.load_months()
        self.copy.setEnabled(False)
        self.export.setEnabled(False)

    def choose_root(self):
        path = QFileDialog.getExistingDirectory(self, '選擇年度照片根目錄', self.root.text())
        if path:
            self.root.setText(path)
            self.load_months()

    def load_months(self):
        previous = self.month.currentText() or self.settings.value('month', '')
        self.month.clear()
        try:
            folders = sorted(p.name for p in Path(self.root.text()).iterdir() if p.is_dir())
            self.month.addItems(folders)
            if previous in folders:
                self.month.setCurrentText(previous)
            self.status.setText(f'已讀取 {len(folders)} 個資料夾，請選擇核對月份。')
        except OSError as exc:
            self.status.setText(f'根目錄無法讀取：{exc}')

    def update_input(self):
        codes, invalid, duplicates = parse_codes(self.input.toPlainText())
        self.input_info.setText(
            f'<b style="color: #c62828;">{len(codes)}</b> 個編號 · '
            f'重複 <b style="color: #c62828;">{len(duplicates)}</b> 筆 · '
            f'無法辨識 <b style="color: #c62828;">{len(invalid)}</b> 筆')

    def run_check(self):
        codes, invalid, _ = parse_codes(self.input.toPlainText())
        if invalid:
            QMessageBox.warning(self, '請修正無法辨識的內容', '\n'.join(invalid[:20]))
            return
        if not codes or not self.month.currentText():
            QMessageBox.information(self, '尚未準備完成', '請輸入編號並選擇月份資料夾。')
            return
        path = str(Path(self.root.text()) / self.month.currentText())
        self.settings.setValue('root', self.root.text())
        self.settings.setValue('month', self.month.currentText())
        self.results = []
        self.render_results()
        self.summary.setText('正在核對…')
        for widget in (self.start, self.root, self.month, self.browse, self.refresh, self.input, self.clear_input, self.copy, self.export):
            widget.setEnabled(False)
        self.status.setText('正在搜尋資料夾及照片，雲端磁碟可能需要較長時間…')
        self.worker = Worker(path, codes)
        self.worker.completed.connect(self.finished_check)
        self.worker.start()

    def finished_check(self, results):
        self.worker.wait()
        for widget in (self.start, self.root, self.month, self.browse, self.refresh, self.input, self.clear_input):
            widget.setEnabled(True)
        if isinstance(results, str):
            self.summary.setText('核對失敗')
            self.status.setText(results)
            return
        self.results = results
        good = sum(r.status == READY for r in results)
        self.summary.setText(
            f'全部 <b style="color: #c62828;">{len(results)}</b> ｜'
            f'已有照片 <b style="color: #c62828;">{good}</b> ｜'
            f'待補／需確認 <b style="color: #c62828;">{len(results) - good}</b>')
        self.filter.setCurrentIndex(0)
        self.render_results()
        self.copy.setEnabled(True)
        self.export.setEnabled(True)
        self.status.setText(f'核對完成：{self.month.currentText()}。已有照片表示存在非空照片檔，未判讀照片內容。')

    def render_results(self):
        mode = self.filter.currentText()
        self.visible_results = [r for r in self.results if mode == '全部' or (r.status == READY) == (mode == '已有照片')]
        self.table.setRowCount(len(self.visible_results))
        for row, r in enumerate(self.visible_results):
            values = [r.code, r.status, str(r.count) if r.count is not None else '—', '\n'.join(r.paths + ([r.detail] if r.detail else []))]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                if col == 1:
                    item.setForeground(QColor('#176b53' if r.status == READY else '#a64218'))
                self.table.setItem(row, col, item)

    def open_folder(self, row, _):
        from PySide6.QtWidgets import QInputDialog
        paths = self.visible_results[row].paths
        if not paths:
            return
        path = paths[0]
        if len(paths) > 1:
            path, ok = QInputDialog.getItem(self, '選擇資料夾', '同編號資料夾', paths, 0, False)
            if not ok:
                return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(path)):
            QMessageBox.warning(self, '無法開啟', path)

    def copy_missing(self):
        text = '\n'.join(f'{r.code}：{r.status}' for r in self.results if r.status != READY)
        QApplication.clipboard().setText(text)
        self.status.setText('待補清單已複製。' if text else '全部編號皆已有照片。')

    def save_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, '匯出核對結果', '滅火器核對結果.csv', 'CSV (*.csv)')
        if path:
            try:
                export_csv(path, self.results)
                self.status.setText(f'已匯出：{path}')
            except OSError as exc:
                QMessageBox.warning(self, '匯出失敗', str(exc))

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.status.setText('核對進行中，請等候完成後再關閉。')
            event.ignore()
        else:
            event.accept()
