# KĀLANĀDAM Manager 🖥️
### Desktop Companion for the KĀLANĀDAM Smart Bell System

KĀLANĀDAM Manager is a Python-based utility designed to manage audio assets and synchronize schedules for the KĀLANĀDAM ESP32 Bell System. It simplifies SD card formatting, folder management, and file naming conventions.

## 🚀 Features
- **SD Card Management:** Automatically creates the required `01/` and `02/` folder structures.
- **Audio Prep:** Validates and renames MP3 files to the required 4-digit format (`0001.mp3`).
- **ESP32 Sync:** Syncs track names and metadata with the ESP32 over Serial/WiFi.
- **User Interface:** Clean, intuitive UI built with PyQt5/PySide.

## 🛠️ Installation
1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv venv