import sys
import os
import json
import shutil
import subprocess
import pygame
import psutil
import urllib.parse
import webbrowser
import keyboard
import pyautogui
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QListWidget, QFileDialog, 
                             QLabel, QComboBox, QMessageBox, QLineEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QObject, QPoint
from PyQt6.QtGui import QPixmap

# --- Path Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
JSON_FILE = os.path.join(BASE_DIR, "games.json")
# Changed to background.png
BG_IMAGE_PATH = os.path.join(BASE_DIR, "background.png")

os.makedirs(IMAGES_DIR, exist_ok=True)

# --- SteamGridDB Search Logic (F9 Tool) ---
class SignalComm(QObject):
    f9_pressed = pyqtSignal()

class SteamGridSearchApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        self.comm = SignalComm()
        self.comm.f9_pressed.connect(self.start_dictation_process)

        # Register Hotkey F9
        keyboard.add_hotkey('f9', lambda: self.comm.f9_pressed.emit())

        # Timer for speech pause (1.5 seconds)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.process_text_and_search)

        self.input_field.textChanged.connect(self.on_text_changed)

    def init_ui(self):
        self.setWindowTitle("SteamGridDB - Direct Grid Search")
        self.setFixedSize(500, 150)
        
        # Center on 1920x1080 Monitor
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

        layout = QVBoxLayout()
        self.label = QLabel("Ready. Press **F9** for Grid search.", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("Waiting for dictation...")
        layout.addWidget(self.input_field)

        self.setLayout(layout)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    def start_dictation_process(self):
        self.activateWindow()
        self.raise_()
        
        # Focus input field (Mouse click simulation)
        rect = self.input_field.geometry()
        center_point = self.input_field.mapToGlobal(QPoint(rect.width() // 2, rect.height() // 2))
        pyautogui.moveTo(center_point.x(), center_point.y(), duration=0.1)
        pyautogui.click()

        # Start Windows Dictation
        time.sleep(0.2)
        pyautogui.hotkey('win', 'h')
        self.label.setText("🎤 Speak now (Searching Grids)...")

    def on_text_changed(self, text):
        if text.strip():
            self.timer.start(1500) 

    def process_text_and_search(self):
        query = self.input_field.text().strip()
        if query:
            encoded_query = urllib.parse.quote(query)
            final_url = f"https://www.steamgriddb.com/search/grids?term={encoded_query}"
            
            self.label.setText(f"Searching Grids for: {query}")
            webbrowser.open(final_url)
            
            # Reset UI after 2 seconds
            QTimer.singleShot(2000, self.reset_ui)

    def reset_ui(self):
        self.input_field.clear()
        self.label.setText("Done. Press F9 again.")

# --- Controller Thread (Pygame) ---
class ControllerThread(QThread):
    sig_left = pyqtSignal()
    sig_right = pyqtSignal()
    sig_a = pyqtSignal()
    sig_y = pyqtSignal()

    def run(self):
        pygame.init()
        pygame.joystick.init()
        
        joystick = None
        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
            print(f"Controller detected: {joystick.get_name()}")
        else:
            print("No controller found.")

        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 4: # LB
                        self.sig_left.emit()
                    elif event.button == 5: # RB
                        self.sig_right.emit()
                    elif event.button == 0: # A
                        self.sig_a.emit()
                    elif event.button == 3: # Y
                        self.sig_y.emit()
            clock.tick(30)

# --- Portrait Display Window ---
class DisplayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: black;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.image_label = QLabel("Loading games...")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("color: white; font-size: 30px; background: transparent;")
        layout.addWidget(self.image_label)
        self.setLayout(layout)
        self.move_to_portrait_monitor()

    def move_to_portrait_monitor(self):
        screens = QApplication.screens()
        target_screen = screens[0]
        for screen in screens:
            size = screen.size()
            if size.width() == 1080 and size.height() == 1920:
                target_screen = screen
                break
        self.setGeometry(target_screen.geometry())
        self.showFullScreen()

    def update_image(self, image_filename):
        if not image_filename:
            self.image_label.setText("No game selected")
            self.image_label.setPixmap(QPixmap())
            return
        img_path = os.path.join(IMAGES_DIR, image_filename)
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            scaled_pixmap = pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("Image not found")

# --- Main Management GUI ---
class GameFrontendMenu(QMainWindow):
    def __init__(self, display_win):
        super().__init__()
        self.setWindowTitle("Game Frontend Manager")
        # 16:9 Aspect Ratio
        self.resize(800, 450) 
        
        self.display_window = display_win
        self.games = self.load_games()
        self.selected_game_idx = 0 if self.games else -1
        self.current_image_path = None
        self.current_game_folder = None
        self.running_process = None 
        self.current_exe_name = None 
        
        self.init_ui()
        
        self.controller_thread = ControllerThread()
        self.controller_thread.sig_left.connect(self.prev_game)
        self.controller_thread.sig_right.connect(self.next_game)
        self.controller_thread.sig_a.connect(self.launch_game)
        self.controller_thread.sig_y.connect(self.quit_frontend)
        self.controller_thread.start()
        
        self.update_display()

    def init_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        style_sheet = """
            QLabel { color: white; font-weight: bold; background-color: rgba(0, 0, 0, 150); padding: 3px; border-radius: 4px; }
            QLineEdit, QComboBox, QPushButton, QListWidget { background-color: rgba(0, 0, 0, 180); border: 2px solid yellow; color: white; padding: 5px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(50, 50, 50, 200); }
        """

        if os.path.exists(BG_IMAGE_PATH):
            css_path = BG_IMAGE_PATH.replace("\\", "/")
            central_widget.setStyleSheet(f"QWidget#CentralWidget {{ border-image: url('{css_path}') 0 0 0 0 stretch stretch; }} {style_sheet}")
        else:
            central_widget.setStyleSheet(f"QWidget#CentralWidget {{ background-color: #2c3e50; }} {style_sheet}")

        main_layout = QVBoxLayout(central_widget)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Game name...")
        main_layout.addWidget(QLabel("1. Game Name:"))
        main_layout.addWidget(self.name_input)

        folder_layout = QVBoxLayout() 
        self.btn_folder = QPushButton("Select Folder")
        self.btn_folder.clicked.connect(self.select_folder)
        self.combo_exe = QComboBox()
        folder_layout.addWidget(self.btn_folder)
        folder_layout.addWidget(self.combo_exe)
        main_layout.addWidget(QLabel("2. Game Directory & EXE:"))
        main_layout.addLayout(folder_layout)

        image_layout = QVBoxLayout()
        self.btn_image = QPushButton("Select Cover")
        self.btn_image.clicked.connect(self.select_image)
        self.lbl_image_path = QLabel("No image selected")
        image_layout.addWidget(self.btn_image)
        image_layout.addWidget(self.lbl_image_path)
        main_layout.addWidget(QLabel("3. Game Cover (Image):"))
        main_layout.addLayout(image_layout)

        self.btn_add = QPushButton("Add Game")
        self.btn_add.clicked.connect(self.add_game)
        main_layout.addWidget(self.btn_add)

        main_layout.addWidget(QLabel("--- List ---"))
        self.game_list_widget = QListWidget()
        self.game_list_widget.setMaximumHeight(150) 
        main_layout.addWidget(self.game_list_widget)
        self.refresh_list()

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.clicked.connect(self.delete_game)
        main_layout.addWidget(self.btn_delete)
        main_layout.addStretch()

    def load_games(self):
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_games(self):
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(self.games, f, indent=4)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.current_game_folder = folder
            self.combo_exe.clear()
            exes = [os.path.join(r, f) for r, d, files in os.walk(folder) for f in files if f.lower().endswith(".exe")]
            if exes: self.combo_exe.addItems(exes)
            else: QMessageBox.warning(self, "Warning", "No .exe found!")

    def select_image(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.bmp)")
        if file:
            self.current_image_path = file
            self.lbl_image_path.setText(os.path.basename(file))

    def add_game(self):
        name, exe = self.name_input.text().strip(), self.combo_exe.currentText()
        if not name or not exe or not self.current_image_path: return
        img_name = os.path.basename(self.current_image_path)
        dest = os.path.join(IMAGES_DIR, img_name)
        if self.current_image_path != dest: shutil.copy2(self.current_image_path, dest)
        self.games.append({"name": name, "folder": self.current_game_folder, "exe": exe, "image_file": img_name})
        self.save_games()
        self.refresh_list()
        self.selected_game_idx = len(self.games) - 1
        self.update_display()

    def refresh_list(self):
        self.game_list_widget.clear()
        for g in self.games: self.game_list_widget.addItem(f"{g['name']} ({os.path.basename(g['exe'])})")

    def is_game_running(self):
        if self.running_process and self.running_process.poll() is None: return True
        if self.current_exe_name:
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() == self.current_exe_name.lower(): return True
                except (psutil.NoSuchProcess, psutil.AccessDenied): continue
        self.running_process, self.current_exe_name = None, None
        return False

    def update_display(self):
        if self.games and 0 <= self.selected_game_idx < len(self.games):
            self.display_window.update_image(self.games[self.selected_game_idx].get("image_file"))

    def prev_game(self):
        if self.is_game_running() or not self.games: return
        self.selected_game_idx = (self.selected_game_idx - 1) % len(self.games)
        self.update_display()

    def next_game(self):
        if self.is_game_running() or not self.games: return
        self.selected_game_idx = (self.selected_game_idx + 1) % len(self.games)
        self.update_display()

    def launch_game(self):
        if self.is_game_running() or not self.games: return
        game = self.games[self.selected_game_idx]
        if os.path.exists(game["exe"]):
            self.current_exe_name = os.path.basename(game["exe"])
            self.running_process = subprocess.Popen(game["exe"], cwd=game["folder"])

    def delete_game(self):
        idx = self.game_list_widget.currentRow()
        if idx >= 0:
            self.games.pop(idx)
            self.save_games()
            self.refresh_list()
            self.selected_game_idx = 0 if self.games else -1
            self.update_display()

    def quit_frontend(self):
        # Prevent quitting if a game is currently running
        if self.is_game_running():
            return
        QApplication.instance().quit()

# --- Execution ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 1. Start SteamGridDB Tool first
    steam_grid_tool = SteamGridSearchApp()
    steam_grid_tool.show()
    
    # 2. Start Main Display and Menu
    portrait_win = DisplayWindow()
    portrait_win.show()
    
    main_menu = GameFrontendMenu(portrait_win)
    main_menu.show()
    
    sys.exit(app.exec())
