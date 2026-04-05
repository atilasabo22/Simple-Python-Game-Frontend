Python Game Frontend & Manager

A lightweight, Python-based game frontend designed to manage and launch your game collection. This tool is specifically optimized for dual-monitor setups (e.g., a main monitor for management and a vertical/portrait monitor for displaying game art).

## 🚀 Features

* **Dual-GUI System:**
    * **Management Window:** Easily add, edit, and delete games from your library.
    * **Portrait Display:** A dedicated, frameless window (optimized for 1080x1920) that displays the currently selected game's cover in full screen.
* **Controller Support:** Navigate through your library and launch games directly with a gamepad (LB/RB to scroll, A to launch, Y to quit).
* **Automated Cover Search (F9 Tool):** An integrated helper tool that triggers Windows Dictation at the press of a button (**F9**) and redirects you directly to matching posters on *SteamGridDB*.
* **Process Management:** The script detects if a game is already running to prevent multiple instances and locks navigation during gameplay.
* **Simple Configuration:** All game data is stored in a local `games.json`, including paths to executables (.exe) and cover images.

## 🛠️ Technologies

* **PyQt6:** For the graphical user interface.
* **Pygame:** For native controller input handling.
* **Psutil & Subprocess:** For monitoring and launching game processes.
* **Pyautogui & Keyboard:** For automating the SteamGridDB search tool.

## 📋 Prerequisites

Before running the script, install the required dependencies:

```bash
pip install PyQt6 pygame psutil keyboard pyautogui
```

## 🎮 How to Use

1.  **Add a Game:** Enter the name, select the installation folder (the .exe will be found automatically), and add a cover image.
2.  **Navigation:** Use your mouse or a connected controller (LB/RB) to scroll through the list. The cover on the second monitor updates in real-time.
3.  **SteamGridDB Tool:** Press **F9**, speak the name of a game, and your browser will immediately open the search results for high-quality grid logos.
   
Video tutorial 

https://youtu.be/ZJOWAeQLvEo?si=oe8dEp71zUaF8w3K

<img width="620" height="503" alt="2026-04-05 17_12_36-Game Frontend Manager" src="https://github.com/user-attachments/assets/6bb25ae9-49a2-48c2-b9dd-dbd01ba81fa9" />

