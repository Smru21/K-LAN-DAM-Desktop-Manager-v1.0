"""
SmartBell Manager — Song Table Widget
"""

import os

from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QWidget, QHBoxLayout, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from ui.styles import COLORS


class SongTable(QTableWidget):
    """Table widget for displaying songs with play/delete buttons."""

    play_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["#", "Song Name", "Status", "Play", "Delete"])

        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.setColumnWidth(0, 60)
        self.setColumnWidth(2, 90)
        self.setColumnWidth(3, 60)
        self.setColumnWidth(4, 60)

        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(True)

        self.setAcceptDrops(True)

        self._play_buttons = {}
        self._playing_row = -1

    def load_songs(self, existing_songs, new_files=None, replacements=None):
        """Populate table with songs."""
        if new_files is None:
            new_files = []
        if replacements is None:
            replacements = {}

        self._play_buttons.clear()
        self._playing_row = -1

        total = len(existing_songs) + len(new_files)
        self.setRowCount(total)

        row = 0

        for number, name in existing_songs:
            is_replacement = name in replacements

            num_item = QTableWidgetItem(number)
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            num_item.setFlags(num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 0, num_item)

            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 1, name_item)

            if is_replacement:
                status = "Replace"
                color = COLORS["orange"]
            else:
                status = "On SD"
                color = COLORS["green"]

            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setForeground(QColor(color))
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 2, status_item)

            self._add_play_button(row)
            self._add_delete_button(row)
            row += 1

        next_number = len(existing_songs) + 1
        for file_path in new_files:
            name = os.path.splitext(os.path.basename(file_path))[0]

            num_item = QTableWidgetItem(f"{next_number:04d}")
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            num_item.setFlags(num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 0, num_item)

            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 1, name_item)

            status_item = QTableWidgetItem("New")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setForeground(QColor(COLORS["blue"]))
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 2, status_item)

            self._add_play_button(row)
            self._add_delete_button(row)
            row += 1
            next_number += 1

    def _add_play_button(self, row):
        btn = QPushButton("▶")
        btn.setFixedSize(40, 28)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['accent']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                font-size: 14px;
                padding: 0;
                min-height: 0;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent']};
                color: #000;
            }}
        """)

        self._play_buttons[row] = btn
        btn.clicked.connect(lambda checked, r=row: self.play_clicked.emit(r))

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(btn)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(2, 2, 2, 2)
        self.setCellWidget(row, 3, container)

    def _add_delete_button(self, row):
        btn = QPushButton("✕")
        btn.setFixedSize(40, 28)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['red']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                padding: 0;
                min-height: 0;
            }}
            QPushButton:hover {{
                background-color: {COLORS['red']};
                color: #fff;
            }}
        """)
        btn.clicked.connect(lambda checked, r=row: self.delete_clicked.emit(r))

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(btn)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(2, 2, 2, 2)
        self.setCellWidget(row, 4, container)

    def set_playing_row(self, row):
        """Set a row as playing — show pause icon."""
        self._reset_playing_button()
        self._playing_row = row

        if row in self._play_buttons:
            self._play_buttons[row].setText("⏸")

    def set_paused_row(self, row):
        """Set a row as paused — show play icon."""
        if row in self._play_buttons:
            self._play_buttons[row].setText("▶")

    def set_resumed_row(self, row):
        """Set a row as resumed — show pause icon."""
        if row in self._play_buttons:
            self._play_buttons[row].setText("⏸")

    def clear_playing(self):
        """Reset all play buttons to default."""
        self._reset_playing_button()
        self._playing_row = -1

    def _reset_playing_button(self):
        """Reset the currently playing button back to play icon."""
        if self._playing_row >= 0 and self._playing_row in self._play_buttons:
            self._play_buttons[self._playing_row].setText("▶")

    def get_selected_rows(self):
        return sorted(set(index.row() for index in self.selectedIndexes()))

    def get_track_number(self, row):
        item = self.item(row, 0)
        return item.text() if item else None

    def get_song_name(self, row):
        item = self.item(row, 1)
        return item.text() if item else None

    def get_status(self, row):
        item = self.item(row, 2)
        return item.text() if item else None

    def filter_rows(self, search_text):
        search = search_text.lower()
        for row in range(self.rowCount()):
            num_item = self.item(row, 0)
            name_item = self.item(row, 1)

            if num_item and name_item:
                text = num_item.text().lower() + " " + name_item.text().lower()
                self.setRowHidden(row, search not in text)
            else:
                self.setRowHidden(row, True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            has_mp3 = any(url.toLocalFile().lower().endswith('.mp3') for url in urls)
            if has_mp3:
                event.acceptProposedAction()
                return
        event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            files = []
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path.lower().endswith('.mp3'):
                    files.append(path)

            if files:
                main_win = self.window()
                if hasattr(main_win, 'handle_dropped_files'):
                    main_win.handle_dropped_files(files)

            event.acceptProposedAction()
        else:
            event.ignore()