"""
SmartBell Manager — Main Window
"""

import os

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QGroupBox,
    QFileDialog, QMessageBox, QSlider, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from ui.styles import APP_STYLE, COLORS
from ui.song_table import SongTable
from core.sd_manager import (
    detect_sd_cards, load_existing_songs, add_songs,
    replace_song, delete_songs, ensure_folders,
    get_file_path, can_add_songs, get_songs_for_sync,
    load_existing_ringtones, add_ringtone, delete_ringtone,
    get_ringtone_file_path, get_next_ringtone_slot,
    MAX_MUSIC_TRACKS, MAX_RINGTONES, RINGTONE_START
)
from core.audio_player import AudioPlayer, format_time
from core.esp32_sync import (
    sync_sounds_to_esp32, sync_school_name_to_esp32,
    check_esp32_connection, DEFAULT_ESP32_IP
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SmartBell SD Card Manager")
        self.setGeometry(100, 50, 950, 900)
        self.setMinimumSize(750, 700)
        self.setMinimumSize(700, 600)
        self.setStyleSheet(APP_STYLE)

        # State
        self.sd_path = ""
        self.existing_songs = []
        self.new_files = []
        self.replacements = {}
        self.existing_ringtones = []

        # Audio player
        self.player = AudioPlayer(self)
        self.player.playback_started.connect(self._on_playback_started)
        self.player.playback_stopped.connect(self._on_playback_stopped)
        self.player.playback_error.connect(self._on_playback_error)
        self.player.position_changed.connect(self._on_position_changed)
        self.player.duration_changed.connect(self._on_duration_changed)

        self._playing_row = -1
        self._playing_file = ""
        self._playing_ringtone_slot = -1

        self._init_ui()

    # ================================================
    #  UI SETUP
    # ================================================
    def _init_ui(self):
        from PyQt6.QtWidgets import QScrollArea

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: {COLORS['bg_dark']};
            }}
        """)

        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        # --- Title ---
        title = QLabel("🔔 SmartBell SD Card Manager")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # --- SD Card Section ---
        sd_group = QGroupBox("📂 SD Card")
        sd_layout = QHBoxLayout()

        self.sd_combo = QComboBox()
        self.sd_combo.setMinimumWidth(120)
        self.sd_combo.setStyleSheet(f"""
            QComboBox {{
                background: {COLORS['bg_input']};
                color: {COLORS['text_white']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background: {COLORS['bg_card']};
                color: {COLORS['text_white']};
                selection-background-color: {COLORS['accent']};
                selection-color: #000;
            }}
        """)

        self.refresh_drives_btn = QPushButton("🔄")
        self.refresh_drives_btn.setFixedWidth(40)
        self.refresh_drives_btn.setToolTip("Refresh drives")
        self.refresh_drives_btn.clicked.connect(self._refresh_drives)

        self.sd_input = QLineEdit()
        self.sd_input.setPlaceholderText("SD card path...")
        self.sd_input.setReadOnly(True)

        self.browse_btn = QPushButton("📁 Browse")
        self.browse_btn.clicked.connect(self._browse_sd)

        self.load_btn = QPushButton("📥 Load")
        self.load_btn.setProperty("class", "success")
        self.load_btn.clicked.connect(self._load_sd)

        sd_layout.addWidget(QLabel("Drive:"))
        sd_layout.addWidget(self.sd_combo)
        sd_layout.addWidget(self.refresh_drives_btn)
        sd_layout.addWidget(self.sd_input, 1)
        sd_layout.addWidget(self.browse_btn)
        sd_layout.addWidget(self.load_btn)
        sd_group.setLayout(sd_layout)
        layout.addWidget(sd_group)

        # --- Add Files + Search Row ---
        action_layout = QHBoxLayout()

        self.add_btn = QPushButton("🎵 Add MP3 Files")
        self.add_btn.clicked.connect(self._add_files)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search songs...")
        self.search_input.textChanged.connect(self._on_search)

        self.count_label = QLabel(f"0 / {MAX_MUSIC_TRACKS} tracks")
        self.count_label.setProperty("class", "status")

        action_layout.addWidget(self.add_btn)
        action_layout.addWidget(self.search_input, 1)
        action_layout.addWidget(self.count_label)
        layout.addLayout(action_layout)

        # --- Song Table (Music) ---
        self.table = SongTable()
        self.table.play_clicked.connect(self._on_play_clicked)
        self.table.delete_clicked.connect(self._on_delete_clicked)
        self.table.setMinimumHeight(280)
        layout.addWidget(self.table, 3)
        # --- Ringtone Section ---
        self._init_ringtone_ui(layout)

        # --- Player Bar ---
        player_group = QGroupBox("🎧 Preview Player")
        player_layout = QHBoxLayout()

        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedWidth(40)
        self.play_btn.clicked.connect(self._toggle_play)

        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setFixedWidth(40)
        self.stop_btn.clicked.connect(self._stop_play)

        self.now_playing_label = QLabel("No song selected")
        self.now_playing_label.setStyleSheet(f"color: {COLORS['text_gray']};")

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setFixedWidth(100)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.sliderMoved.connect(self._on_seek)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.valueChanged.connect(self._on_volume)

        vol_label = QLabel("🔊")

        player_layout.addWidget(self.play_btn)
        player_layout.addWidget(self.stop_btn)
        player_layout.addWidget(self.now_playing_label, 1)
        player_layout.addWidget(self.time_label)
        player_layout.addWidget(self.seek_slider, 2)
        player_layout.addWidget(vol_label)
        player_layout.addWidget(self.volume_slider)
        player_group.setLayout(player_layout)
        layout.addWidget(player_group)

        # --- Bottom Buttons ---
        bottom_layout = QHBoxLayout()

        self.delete_sel_btn = QPushButton("🗑️ Delete Selected")
        self.delete_sel_btn.setProperty("class", "danger")
        self.delete_sel_btn.clicked.connect(self._delete_selected)

        self.build_btn = QPushButton("💾 Build / Update SD")
        self.build_btn.setProperty("class", "accent")
        self.build_btn.clicked.connect(self._build_sd)

        bottom_layout.addWidget(self.delete_sel_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.build_btn)
        layout.addLayout(bottom_layout)

        # --- ESP32 Sync Section ---
        sync_group = QGroupBox("📡 Sync to ESP32")
        sync_layout = QHBoxLayout()

        self.ip_input = QLineEdit(DEFAULT_ESP32_IP)
        self.ip_input.setMaximumWidth(150)
        self.ip_input.setPlaceholderText("ESP32 IP")

        self.check_btn = QPushButton("🔍 Check")
        self.check_btn.clicked.connect(self._check_esp32)

        self.sync_btn = QPushButton("📡 Sync Sounds")
        self.sync_btn.setProperty("class", "success")
        self.sync_btn.clicked.connect(self._sync_to_esp32)

        self.esp_status = QLabel("Not connected")
        self.esp_status.setProperty("class", "status")

        sync_layout.addWidget(QLabel("IP:"))
        sync_layout.addWidget(self.ip_input)
        sync_layout.addWidget(self.check_btn)
        sync_layout.addWidget(self.sync_btn)
        sync_layout.addWidget(self.esp_status, 1)
        sync_group.setLayout(sync_layout)
        layout.addWidget(sync_group)

        # --- Status Bar ---
        self.status_label = QLabel("Ready — Select SD card to begin")
        self.status_label.setProperty("class", "status")
        layout.addWidget(self.status_label)

        QTimer.singleShot(100, self._refresh_drives)

    # ================================================
    #  RINGTONE UI
    # ================================================
    def _init_ringtone_ui(self, parent_layout):
        self.ringtone_group = QGroupBox(f"🔔 Bell Ringtones (0 / {MAX_RINGTONES})")
        ring_layout = QVBoxLayout()

        # Ringtone table
        self.ring_table = QTableWidget()
        self.ring_table.setColumnCount(5)
        self.ring_table.setHorizontalHeaderLabels(["Slot", "Name", "Status", "Play", "Delete"])
        self.ring_table.setRowCount(MAX_RINGTONES)
        self.ring_table.setMinimumHeight(180)
        self.ring_table.setMaximumHeight(250)
        self.ring_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.ring_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.ring_table.verticalHeader().setVisible(False)
        self.ring_table.setShowGrid(False)

        header = self.ring_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.ring_table.setColumnWidth(0, 40)
        self.ring_table.setColumnWidth(2, 60)
        self.ring_table.setColumnWidth(3, 50)
        self.ring_table.setColumnWidth(4, 50)

        self.ring_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text_white']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                gridline-color: transparent;
            }}
            QTableWidget::item {{
                padding: 2px 4px;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_gray']};
                border: none;
                padding: 4px;
                font-size: 11px;
            }}
        """)

        ring_layout.addWidget(self.ring_table)

        # Add ringtone button
        ring_btn_layout = QHBoxLayout()

        self.add_ring_btn = QPushButton("🔔 Add Ringtone")
        self.add_ring_btn.clicked.connect(self._add_ringtone)

        ring_btn_layout.addWidget(self.add_ring_btn)
        ring_btn_layout.addStretch()

        ring_layout.addLayout(ring_btn_layout)

        self.ringtone_group.setLayout(ring_layout)
        parent_layout.addWidget(self.ringtone_group, 0)    # ★ stretch 0 = no expand

        # Initialize empty slots
        self._refresh_ringtone_table()

    def _refresh_ringtone_table(self):
        """Refresh ringtone table to show all 10 slots."""
        if self.sd_path:
            self.existing_ringtones = load_existing_ringtones(self.sd_path)
        else:
            self.existing_ringtones = []

        # Build lookup: slot -> (number, name)
        ring_map = {}
        for slot, number, name in self.existing_ringtones:
            ring_map[slot] = (number, name)

        for row in range(MAX_RINGTONES):
            slot = row + 1

            # Slot number
            slot_item = QTableWidgetItem(str(slot))
            slot_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ring_table.setItem(row, 0, slot_item)

            if slot in ring_map:
                number, name = ring_map[slot]

                # Name
                name_item = QTableWidgetItem(name)
                self.ring_table.setItem(row, 1, name_item)

                # Status
                status_item = QTableWidgetItem("On SD")
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                status_item.setForeground(QColor(COLORS['green']))
                self.ring_table.setItem(row, 2, status_item)

                # Play button
                play_btn = QPushButton("▶")
                play_btn.setFixedHeight(26)
                play_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {COLORS['green']};
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 12px;
                        padding: 2px;
                    }}
                    QPushButton:hover {{ background: #45a049; }}
                """)
                play_btn.clicked.connect(lambda checked, s=slot: self._play_ringtone(s))
                self.ring_table.setCellWidget(row, 3, play_btn)

                # Delete button
                del_btn = QPushButton("✕")
                del_btn.setFixedHeight(26)
                del_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {COLORS['red']};
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 12px;
                        padding: 2px;
                    }}
                    QPushButton:hover {{ background: #d32f2f; }}
                """)
                del_btn.clicked.connect(lambda checked, s=slot: self._delete_ringtone(s))
                self.ring_table.setCellWidget(row, 4, del_btn)

            else:
                # Empty slot
                name_item = QTableWidgetItem("— Empty —")
                name_item.setForeground(QColor(COLORS['text_gray']))
                self.ring_table.setItem(row, 1, name_item)

                status_item = QTableWidgetItem("Empty")
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                status_item.setForeground(QColor(COLORS['text_gray']))
                self.ring_table.setItem(row, 2, status_item)

                # Add button instead of play
                add_btn = QPushButton("+")
                add_btn.setFixedHeight(26)
                add_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {COLORS['accent']};
                        color: black;
                        border: none;
                        border-radius: 4px;
                        font-size: 14px;
                        font-weight: bold;
                        padding: 2px;
                    }}
                    QPushButton:hover {{ background: #e6c200; }}
                """)
                add_btn.clicked.connect(lambda checked, s=slot: self._add_ringtone_to_slot(s))
                self.ring_table.setCellWidget(row, 3, add_btn)

                # No delete for empty
                self.ring_table.removeCellWidget(row, 4)
                empty_del = QTableWidgetItem("")
                self.ring_table.setItem(row, 4, empty_del)

        filled = len(self.existing_ringtones)
        self.ringtone_group.setTitle(f"🔔 Bell Ringtones ({filled} / {MAX_RINGTONES})")

    def _add_ringtone(self):
        """Add ringtone to next available slot."""
        if not self.sd_path:
            QMessageBox.warning(self, "Error", "Load SD card first.")
            return

        next_slot = get_next_ringtone_slot(self.existing_ringtones)
        if next_slot is None:
            QMessageBox.warning(self, "Full", f"All {MAX_RINGTONES} ringtone slots are used.")
            return

        self._add_ringtone_to_slot(next_slot)

    def _add_ringtone_to_slot(self, slot):
        """Add ringtone to a specific slot."""
        if not self.sd_path:
            QMessageBox.warning(self, "Error", "Load SD card first.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Select Ringtone for Slot {slot}", "", "MP3 Files (*.mp3)"
        )
        if not file_path:
            return

        self.player.stop()
        self._playing_ringtone_slot = -1

        try:
            result = add_ringtone(self.sd_path, file_path, slot)
            if result:
                s, num, name = result
                self._refresh_ringtone_table()
                self.status_label.setText(f"Ringtone {s} added: {name}")
            else:
                QMessageBox.warning(self, "Error", "Failed to add ringtone.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add ringtone:\n{e}")

    def _delete_ringtone(self, slot):
        """Delete ringtone from slot."""
        # Find name for display
        name = f"Ringtone {slot}"
        for s, num, n in self.existing_ringtones:
            if s == slot:
                name = n
                break

        reply = QMessageBox.question(
            self, "Delete Ringtone",
            f'Delete "{name}" from slot {slot}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.player.stop()
        self._playing_ringtone_slot = -1

        try:
            delete_ringtone(self.sd_path, slot)
            self._refresh_ringtone_table()
            self.status_label.setText(f"Ringtone {slot} deleted")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete ringtone:\n{e}")

    def _play_ringtone(self, slot):
        """Preview a ringtone."""
        if not self.sd_path:
            return

        # If same slot playing, toggle
        if slot == self._playing_ringtone_slot:
            if self.player.is_playing():
                self.player.pause()
                self.play_btn.setText("▶")
                return
            elif self.player.is_paused():
                self.player.resume()
                self.play_btn.setText("⏸")
                return

        file_path = get_ringtone_file_path(self.sd_path, slot)
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Error", f"Ringtone file not found:\n{file_path}")
            return

        self._playing_row = -1
        self._playing_ringtone_slot = slot
        self._playing_file = file_path
        self.table.clear_playing()
        self.player.play(file_path)

    # ================================================
    #  SD CARD
    # ================================================
    def _refresh_drives(self):
        self.sd_combo.clear()
        drives = detect_sd_cards()
        if drives:
            for d in drives:
                self.sd_combo.addItem(d)
            self.sd_input.setText(drives[0])
            self.status_label.setText(f"Found {len(drives)} removable drive(s)")
        else:
            self.sd_combo.addItem("No drives found")
            self.status_label.setText("No removable drives detected — use Browse")

        self.sd_combo.currentTextChanged.connect(self._on_drive_selected)

    def _on_drive_selected(self, text):
        if text and not text.startswith("No "):
            self.sd_input.setText(text)

    def _browse_sd(self):
        folder = QFileDialog.getExistingDirectory(self, "Select SD Card Root Folder")
        if folder:
            self.sd_input.setText(folder)
            self._load_from_path(folder)

    def _load_sd(self):
        path = self.sd_input.text().strip()
        if not path or path.startswith("No "):
            QMessageBox.warning(self, "Error", "Select a valid SD card path first.")
            return
        self._load_from_path(path)

    def _load_from_path(self, path):
        if not os.path.exists(path):
            QMessageBox.warning(self, "Error", f"Path does not exist: {path}")
            return

        self.sd_path = path
        self.new_files = []
        self.replacements = {}
        self.player.stop()
        self._playing_row = -1
        self._playing_ringtone_slot = -1

        self.existing_songs = load_existing_songs(self.sd_path)
        self._refresh_table()
        self._refresh_ringtone_table()

        count = len(self.existing_songs)
        ring_count = len(self.existing_ringtones)
        self.status_label.setText(
            f"Loaded {count} songs + {ring_count} ringtones from {path}"
        )

    def _refresh_table(self):
        self.table.load_songs(self.existing_songs, self.new_files, self.replacements)
        total = len(self.existing_songs) + len(self.new_files)
        self.count_label.setText(f"{total} / {MAX_MUSIC_TRACKS} tracks")

    # ================================================
    #  ADD FILES
    # ================================================
    def _add_files(self):
        if not self.sd_path:
            QMessageBox.warning(self, "Error", "Load SD card first.")
            return

        files, _ = QFileDialog.getOpenFileNames(
            self, "Select MP3 Files", "", "MP3 Files (*.mp3)"
        )
        if not files:
            return

        self._process_new_files(files)

    def handle_dropped_files(self, files):
        if not self.sd_path:
            QMessageBox.warning(self, "Error", "Load SD card first.")
            return
        self._process_new_files(files)

    def _process_new_files(self, files):
        if not can_add_songs(self.existing_songs, len(files) + len(self.new_files)):
            QMessageBox.warning(
                self, "Limit Reached",
                f"Cannot add {len(files)} files. Maximum is {MAX_MUSIC_TRACKS} music tracks."
            )
            return

        existing_names = {name: number for number, name in self.existing_songs}
        added = 0
        replaced = 0

        for file in files:
            name = os.path.splitext(os.path.basename(file))[0]

            if name in existing_names:
                reply = QMessageBox.question(
                    self, "Duplicate Detected",
                    f'"{name}" already exists as track {existing_names[name]}.\n\nReplace it?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.replacements[name] = file
                    replaced += 1
            else:
                total = len(self.existing_songs) + len(self.new_files) + 1
                if total > MAX_MUSIC_TRACKS:
                    QMessageBox.warning(self, "Limit", f"Maximum {MAX_MUSIC_TRACKS} music tracks reached.")
                    break
                self.new_files.append(file)
                added += 1

        self._refresh_table()
        self.status_label.setText(f"Added {added} new, {replaced} replacements queued")

    # ================================================
    #  DELETE
    # ================================================
    def _on_delete_clicked(self, row):
        name = self.table.get_song_name(row)
        if not name:
            return

        reply = QMessageBox.question(
            self, "Delete Song",
            f'Delete "{name}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._delete_rows([row])

    def _delete_selected(self):
        rows = self.table.get_selected_rows()
        if not rows:
            QMessageBox.warning(self, "Warning", "Select at least one song.")
            return

        reply = QMessageBox.question(
            self, "Delete Songs",
            f"Delete {len(rows)} selected song(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._delete_rows(rows)

    def _delete_rows(self, rows):
        self.player.release()
        self._playing_row = -1
        self._playing_ringtone_slot = -1

        existing_count = len(self.existing_songs)
        existing_to_delete = []
        new_to_delete = []

        for row in sorted(rows, reverse=True):
            status = self.table.get_status(row)

            if status in ("On SD", "Replace"):
                number = self.table.get_track_number(row)
                name = self.table.get_song_name(row)
                if number:
                    existing_to_delete.append(number)
                if name and name in self.replacements:
                    del self.replacements[name]
            elif status == "New":
                new_idx = row - existing_count
                if 0 <= new_idx < len(self.new_files):
                    new_to_delete.append(new_idx)

        for idx in sorted(new_to_delete, reverse=True):
            self.new_files.pop(idx)

        if existing_to_delete and self.sd_path:
            try:
                delete_songs(self.sd_path, existing_to_delete)
            except PermissionError:
                import time
                time.sleep(0.5)
                try:
                    delete_songs(self.sd_path, existing_to_delete)
                except Exception as e:
                    QMessageBox.critical(
                        self, "Error",
                        f"Cannot delete — file is still in use.\n\n"
                        f"Close any other programs using the SD card and try again.\n\n"
                        f"Error: {e}"
                    )
                    return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Delete failed: {e}")
                return

        if self.sd_path:
            self.existing_songs = load_existing_songs(self.sd_path)

        self._refresh_table()
        total_deleted = len(existing_to_delete) + len(new_to_delete)
        self.status_label.setText(f"Deleted {total_deleted} song(s) — files renumbered")

    # ================================================
    #  BUILD SD CARD
    # ================================================
    def _build_sd(self):
        if not self.sd_path:
            QMessageBox.warning(self, "Error", "Load SD card first.")
            return

        if not self.new_files and not self.replacements:
            QMessageBox.information(self, "Info", "Nothing to update. SD card is current.")
            return

        self.player.stop()
        self._playing_row = -1
        self._playing_ringtone_slot = -1

        try:
            ensure_folders(self.sd_path)

            for name, file_path in self.replacements.items():
                for number, song_name in self.existing_songs:
                    if song_name == name:
                        replace_song(self.sd_path, number, file_path)
                        break

            if self.new_files:
                added = add_songs(self.sd_path, self.new_files, self.existing_songs)
                self.status_label.setText(
                    f"Added {len(added)} songs, {len(self.replacements)} replaced"
                )
            else:
                self.status_label.setText(f"Replaced {len(self.replacements)} songs")

            self.new_files = []
            self.replacements = {}

            self.existing_songs = load_existing_songs(self.sd_path)
            self._refresh_table()
            self._refresh_ringtone_table()

            self._auto_sync()

            QMessageBox.information(self, "Success", "SD Card updated successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Build failed:\n{e}")

    def _auto_sync(self):
        ip = self.ip_input.text().strip()
        connected, _ = check_esp32_connection(ip)
        if connected:
            sounds = get_songs_for_sync(self.sd_path)
            success, msg = sync_sounds_to_esp32(sounds, ip)
            if success:
                self.esp_status.setText(f"✅ Auto-synced {len(sounds)} names")
                self.esp_status.setStyleSheet(f"color: {COLORS['green']};")
            else:
                self.esp_status.setText("⚠️ Auto-sync failed")
                self.esp_status.setStyleSheet(f"color: {COLORS['orange']};")

    # ================================================
    #  AUDIO PLAYER
    # ================================================
    def _on_play_clicked(self, row):
        status = self.table.get_status(row)
        number = self.table.get_track_number(row)
        name = self.table.get_song_name(row)

        if not name:
            return

        # Same row: toggle pause/resume
        if row == self._playing_row:
            if self.player.is_playing():
                self.player.pause()
                self.play_btn.setText("▶")
                self.table.set_paused_row(row)
                return
            elif self.player.is_paused():
                self.player.resume()
                self.play_btn.setText("⏸")
                self.table.set_resumed_row(row)
                return

        # Different row or stopped: play new track
        file_path = ""

        if status == "New":
            new_idx = row - len(self.existing_songs)
            if 0 <= new_idx < len(self.new_files):
                file_path = self.new_files[new_idx]

        elif status == "Replace" and name in self.replacements:
            file_path = self.replacements[name]

        elif status == "On SD" and self.sd_path:
            file_path = get_file_path(self.sd_path, number)

        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Error", f"File not found:\n{file_path}")
            return

        self._playing_row = row
        self._playing_ringtone_slot = -1
        self._playing_file = file_path
        self.player.play(file_path)

    def _toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
            self.play_btn.setText("▶")
            if self._playing_row >= 0:
                self.table.set_paused_row(self._playing_row)
        elif self.player.is_paused():
            self.player.resume()
            self.play_btn.setText("⏸")
            if self._playing_row >= 0:
                self.table.set_resumed_row(self._playing_row)

    def _stop_play(self):
        self.player.stop()
        self._playing_row = -1
        self._playing_ringtone_slot = -1

    def _on_playback_started(self, file_path):
        name = os.path.splitext(os.path.basename(file_path))[0]
        if self._playing_ringtone_slot > 0:
            self.now_playing_label.setText(f"🔔 Ringtone {self._playing_ringtone_slot}: {name}")
        else:
            self.now_playing_label.setText(f"♫ {name}")
        self.now_playing_label.setStyleSheet(f"color: {COLORS['accent']};")
        self.play_btn.setText("⏸")
        if self._playing_row >= 0:
            self.table.set_playing_row(self._playing_row)

    def _on_playback_stopped(self):
        self.now_playing_label.setText("No song selected")
        self.now_playing_label.setStyleSheet(f"color: {COLORS['text_gray']};")
        self.play_btn.setText("▶")
        self.time_label.setText("00:00 / 00:00")
        self.seek_slider.setRange(0, 0)
        self.seek_slider.setValue(0)
        self.table.clear_playing()
        self._playing_row = -1
        self._playing_ringtone_slot = -1

    def _on_playback_error(self, error):
        self.status_label.setText(f"Player error: {error}")

    def _on_position_changed(self, position):
        duration = self.player.get_duration()
        self.time_label.setText(f"{format_time(position)} / {format_time(duration)}")
        if not self.seek_slider.isSliderDown():
            self.seek_slider.setValue(position)

    def _on_duration_changed(self, duration):
        self.seek_slider.setRange(0, duration)

    def _on_seek(self, position):
        self.player.set_position(position)

    def _on_volume(self, value):
        self.player.set_volume(value / 100.0)

    def _on_search(self, text):
        self.table.filter_rows(text)

        # ================================================
    #  ESP32 SYNC
    # ================================================
    def _check_esp32(self):
        ip = self.ip_input.text().strip()
        self.esp_status.setText("Checking...")
        self.esp_status.setStyleSheet(f"color: {COLORS['text_gray']};")

        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        connected, result = check_esp32_connection(ip)

        if connected:
            state = result.get("state", "unknown")
            events = result.get("events", 0)
            self.esp_status.setText(f"✅ Connected — {state}, {events} events")
            self.esp_status.setStyleSheet(f"color: {COLORS['green']};")
        else:
            self.esp_status.setText(f"❌ {result}")
            self.esp_status.setStyleSheet(f"color: {COLORS['red']};")

    def _sync_to_esp32(self):
        ip = self.ip_input.text().strip()

        if not self.sd_path:
            QMessageBox.warning(self, "Error", "No SD card loaded.")
            return

        if not self.existing_songs and not self.existing_ringtones:
            QMessageBox.warning(self, "Error", "No songs or ringtones loaded. Load SD card first.")
            return

        sounds = get_songs_for_sync(self.sd_path)

        if not sounds:
            QMessageBox.warning(self, "Error", "No tracks found to sync.")
            return

        self.esp_status.setText("Syncing...")
        self.esp_status.setStyleSheet(f"color: {COLORS['text_gray']};")

        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        success, msg = sync_sounds_to_esp32(sounds, ip)

        if success:
            music_count = len(self.existing_songs)
            ring_count = len(self.existing_ringtones)
            self.esp_status.setText(
                f"✅ Synced {music_count} songs + {ring_count} ringtones"
            )
            self.esp_status.setStyleSheet(f"color: {COLORS['green']};")
            QMessageBox.information(
                self, "Sync Success",
                f"Successfully synced to ESP32:\n\n"
                f"• {music_count} music tracks\n"
                f"• {ring_count} bell ringtones\n\n"
                f"Total: {len(sounds)} track names sent."
            )
        else:
            self.esp_status.setText(f"❌ {msg}")
            self.esp_status.setStyleSheet(f"color: {COLORS['red']};")
            QMessageBox.warning(
                self, "Sync Failed",
                f"{msg}\n\nMake sure:\n"
                f"• You're connected to SmartBell WiFi\n"
                f"• ESP32 is powered on\n"
                f"• IP address is correct\n"
                f"• /api/sounds endpoint exists on ESP32"
            )

    # ================================================
    #  WINDOW CLOSE
    # ================================================
    def closeEvent(self, event):
        self.player.stop()

        if self.new_files or self.replacements:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have pending changes that haven't been built to SD card.\n\n"
                "Close anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

        event.accept()