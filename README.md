# KĀLANĀDAM Manager 🖥️
### Desktop Companion for the KĀLANĀDAM Smart Bell System

KĀLANĀDAM Manager is a Python-based desktop utility designed to manage audio assets and synchronize schedules for the KĀLANĀDAM ESP32 Bell System.

---

## 🔧 Core Requirement
This application is designed specifically to work with the **KĀLANĀDAM Firmware**. The firmware must be installed on your ESP32 hardware for full system functionality.

👉 **[Get the KĀLANĀDAM Firmware Here](https://github.com/Smru21/Kaalanadham)**

---

## 🚀 Features
- **SD Card Management:** Automatically creates the required `01/` and `02/` folder structures.
- **Audio Validation:** Renames and formats MP3 files to the hardware-required 4-digit standard (`0001.mp3`).
- **Metadata Sync:** (Optional) Syncs track names with the ESP32 over Serial/WiFi.
- **Cross-Platform:** Built with PyQt6 for a smooth desktop experience.

## 🛠️ Installation
1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
