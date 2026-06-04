"""
SmartBell Manager — MP3 Preview Player
Uses PyQt6 QMediaPlayer for audio playback.
"""

import time
from PyQt6.QtCore import QUrl, QObject, pyqtSignal
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput


class AudioPlayer(QObject):
    """Simple MP3 player for previewing songs."""

    playback_started = pyqtSignal(str)
    playback_stopped = pyqtSignal()
    playback_error = pyqtSignal(str)
    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)

        self._current_file = ""
        self._switching = False
        self._audio_output.setVolume(0.7)

        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.errorOccurred.connect(self._on_error)
        self._player.playbackStateChanged.connect(self._on_state_changed)

    def play(self, file_path):
        """Play an MP3 file. Stops current playback first."""
        self._switching = True

        if self._player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self._player.stop()

        self._current_file = file_path
        self._player.setSource(QUrl.fromLocalFile(file_path))
        self._player.play()

        self._switching = False
        self.playback_started.emit(file_path)

    def stop(self):
        """Stop playback."""
        was_playing = self._current_file != ""
        self._current_file = ""
        self._switching = True

        if self._player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self._player.stop()

        # Clear the source to release the file handle
        self._player.setSource(QUrl())

        self._switching = False

        if was_playing:
            self.playback_stopped.emit()

    def release(self):
        """Fully release any file handles. Call before deleting files."""
        self._current_file = ""
        self._switching = True

        self._player.stop()
        self._player.setSource(QUrl())

        # Process events and small delay to ensure OS releases file
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        time.sleep(0.1)
        QApplication.processEvents()

        self._switching = False

    def pause(self):
        """Pause playback."""
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()

    def resume(self):
        """Resume paused playback."""
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self._player.play()

    def set_volume(self, volume):
        self._audio_output.setVolume(max(0.0, min(1.0, volume)))

    def get_volume(self):
        return self._audio_output.volume()

    def set_position(self, position_ms):
        self._player.setPosition(position_ms)

    def get_position(self):
        return self._player.position()

    def get_duration(self):
        return self._player.duration()

    def is_playing(self):
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def is_paused(self):
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PausedState

    def is_stopped(self):
        return self._player.playbackState() == QMediaPlayer.PlaybackState.StoppedState

    def current_file(self):
        return self._current_file

    def _on_position_changed(self, position):
        self.position_changed.emit(position)

    def _on_duration_changed(self, duration):
        self.duration_changed.emit(duration)

    def _on_error(self, error):
        error_msg = self._player.errorString()
        print(f"[Player] Error: {error_msg}")
        self.playback_error.emit(error_msg)

    def _on_state_changed(self, state):
        if self._switching:
            return
        if state == QMediaPlayer.PlaybackState.StoppedState:
            if self._current_file:
                self._current_file = ""
                self.playback_stopped.emit()


def format_time(ms):
    if ms < 0:
        ms = 0
    seconds = ms // 1000
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"