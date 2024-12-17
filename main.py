import os
import subprocess
import sys
import threading
import uuid
import json
import random
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import *
import requests
from mojang import *
import minecraft_launcher_lib
import webbrowser
import pygetwindow as gw
import time
import ctypes

selected_version = "1.8.9"
loggedin = False
account = {}
data = {
    "account": {
        "access_token": "",
        "username": "",
        "id": ""
    },
    "settings": {
        "hide_window_when_startup": "",
        "theme": ""
    },
    "version": ""
}
starting = False
hide_window_on_startup = "true"
file_name = ""

class Ui(QMainWindow):
    def __init__(self):
        self.minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
        super(Ui, self).__init__()
        self.setWindowTitle("IT Client")
        self.setFixedSize(765, 443)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.init_ui()

    def init_ui(self):
        global selected_version, account, hide_window_on_startup, file_name
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        self.main_ui = QMainWindow()
        uic.loadUi('ui\\Design.ui', self.main_ui)
        self.stack.addWidget(self.main_ui)

        self.main_ui.start_game.setText(f"LAUNCH {selected_version}")

        self.login_ui = QMainWindow()
        uic.loadUi('ui\\Login.ui', self.login_ui)
        self.stack.addWidget(self.login_ui)

        self.settings_ui = QMainWindow()
        uic.loadUi('ui\\Settings.ui', self.settings_ui)
        self.stack.addWidget(self.settings_ui)

        if os.path.exists("json\\config.json"):
            with open("json\\config.json", 'r') as f:
                config = json.load(f)
            account = config.get("account", {})
            settings_config = config.get("settings", {})
            if account != {}:
                username = account.get("username")
                self.main_ui.Profile.setText(f"Hello, {username}")
                self.settings_ui.Profile.setText(f"Hello, {username}")
            selected_version = config.get("version")
            self.main_ui.start_game.setText(f"LAUNCH {selected_version}")
            theme_path = settings_config.get("theme", "")
            if theme_path and os.path.exists(theme_path):
                try:
                    with open(theme_path, 'r') as f:
                        theme = json.load(f)
                    self.apply_theme(theme)
                except Exception as e:
                    print(f"Failed to load theme: {e}")

            hide_window_on_startup = settings_config.get("hide_window_when_startup")
            if hide_window_on_startup == "true":
                self.settings_ui.hide_window_button.setText("Enabled")
            else:
                self.settings_ui.hide_window_button.setText("Disabled")
            file_name = settings_config.get("theme")

        self.main_ui.findChild(QPushButton, 'Profile').clicked.connect(self.switch_to_login)
        self.settings_ui.findChild(QPushButton, 'Profile').clicked.connect(self.switch_to_login)
        self.login_ui.findChild(QPushButton, 'back').clicked.connect(self.switch_to_main)
        self.main_ui.findChild(QPushButton, 'start_game').clicked.connect(self.launch_minecraft_threaded)
        self.login_ui.findChild(QPushButton, 'Login_2').clicked.connect(self.play_offline)
        self.main_ui.findChild(QPushButton, 'v189').clicked.connect(self.switch_to_189)
        self.main_ui.findChild(QPushButton, 'v1122').clicked.connect(self.switch_to_1122)
        self.login_ui.username.max_length = 20
        self.login_ui.username.textChanged.connect(self.enforce_max_length)
        self.main_ui.frame_2.hide()
        self.main_ui.findChild(QPushButton, 'close').clicked.connect(self.close)
        self.main_ui.hide.clicked.connect(self.window().showMinimized)
        self.login_ui.findChild(QPushButton, 'close').clicked.connect(self.close)
        self.login_ui.hide.clicked.connect(self.window().showMinimized)
        self.settings_ui.findChild(QPushButton, 'close').clicked.connect(self.close)
        self.settings_ui.hide.clicked.connect(self.window().showMinimized)
        self.main_ui.Versions.hide()
        self.main_ui.Settings_button.clicked.connect(self.switch_to_settings)
        self.settings_ui.Home_Button_2.clicked.connect(self.switch_to_main_home)
        self.settings_ui.Version_button.clicked.connect(self.switch_to_main_versions)
        self.settings_ui.theme_button.clicked.connect(self.load_skin)
        self.settings_ui.hide_window_button.clicked.connect(self.hide_window)

    def hide_window(self):
        if hide_window_on_startup == "true":
            self.enable_disable_hide_window()
            self.settings_ui.hide_window_button.setText("Enabled")
        else:
            self.enable_disable_hide_window()
            self.settings_ui.hide_window_button.setText("Disabled")

    def enforce_max_length(self):
        text = self.login_ui.username.toPlainText()
        if len(text) > self.login_ui.username.max_length:
            self.login_ui.username.setPlainText(text[:self.login_ui.username.max_length])

    def enable_disable_hide_window(self):
        global hide_window_on_startup
        self.savedata()
        if hide_window_on_startup == "true":
            hide_window_on_startup = "false"
        else:
            hide_window_on_startup = "true"

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            event.ignore()
        else:
            super(Ui, self).keyPressEvent(event)

    def switch_to_login(self):
        self.stack.setCurrentWidget(self.login_ui)

    def switch_to_settings(self):
        self.stack.setCurrentWidget(self.settings_ui)

    def switch_to_189(self):
        global starting, selected_version
        if starting == False:
            selected_version = "1.8.9"
            self.main_ui.start_game.setText(f"LAUNCH {selected_version}")
            self.switch_to_main()
            self.savedata()
    
    def switch_to_1122(self):
        global starting, selected_version
        if starting == False:
            selected_version = "1.12.2"
            self.main_ui.start_game.setText(f"LAUNCH {selected_version}")
            self.switch_to_main()
            self.savedata()

    def switch_to_main(self):
        global account
        self.stack.setCurrentWidget(self.main_ui)
        username = account.get("username")
        if username:
            self.main_ui.Profile.setText(f"Hello, {username}")
            self.settings_ui.Profile.setText(f"Hello, {username}")
    
    def switch_to_main_home(self):
        global account
        self.main_ui.Home.show()
        self.main_ui.Versions.hide()
        self.main_ui.frame.show()
        self.main_ui.frame_2.hide()
        self.stack.setCurrentWidget(self.main_ui)
        username = account.get("username")
        if username:
            self.main_ui.Profile.setText(f"Hello, {username}")

    def switch_to_main_versions(self):
        self.main_ui.Home.hide()
        self.main_ui.Versions.show()
        self.main_ui.frame.hide()
        self.main_ui.frame_2.show()
        global account
        self.stack.setCurrentWidget(self.main_ui)
        username = account.get("username")
        if username:
            self.main_ui.Profile.setText(f"Hello, {username}")

    def savedata(self):
        global selected_version, account, hide_window_on_startup, file_name
        print("SAVING CONFIG")
        data = {
            "account": account,
            "settings": {
                "hide_window_when_startup": hide_window_on_startup,
                "theme": file_name
            },
            "version": selected_version
        }
        try:
            with open("json\\config.json", 'w') as f:
                json.dump(data, f, indent=4)
            print("SAVED SUCCESSFULLY")
            print(data)
        except:
            print("CANNOT SAVE")

    def play_offline(self):
        global account, data
        username = self.login_ui.findChild(QTextEdit, 'username').toPlainText()
        if username:
            account = {"access_token": "offline_mode", "username": username, "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, username))}
            self.switch_to_main()
            loggedin = True
            self.savedata()

    def apply_theme(self, theme_data):
        try:
            background_color = theme_data.get("background_color", "rgb(43, 43, 43)")
            button_color = theme_data.get("button_color", "rgb(36, 157, 0)")
            button_border_radius = theme_data.get("button_border_radius", "10px")
            button_text_color = theme_data.get("button_text_color", "#ffffff")
            title_bar_color = theme_data.get("title_bar_color", "rgb(74, 74, 74)")
            title_bar_button_color = theme_data.get("title_bar_button_color", "white")
            logo_color = theme_data.get("logo_color", "white")
            profile_button_color = theme_data.get("profile_button_color", "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgb(130, 130, 130), stop:1 rgb(171, 171, 171))")
            profile_button_text_color = theme_data.get("profile_button_text_color", "white")
            settings_item_background_color = theme_data.get("settings_item_background_color", "rgb(36, 36, 36)")
            settings_item_text_color = theme_data.get("settings_item_text_color", "white")

            self.main_ui.setStyleSheet(f"background-color: {background_color};")
            self.login_ui.setStyleSheet(f"background-color: {background_color};")
            self.settings_ui.setStyleSheet(f"background-color: {background_color};")
            self.main_ui.titlebar.setStyleSheet(f"background-color: {title_bar_color};")
            self.main_ui.hide.setStyleSheet(f"color: {title_bar_button_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px;")
            self.main_ui.close.setStyleSheet(f"color: {title_bar_button_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px;")
            self.main_ui.Title.setStyleSheet(f"color: {logo_color}")
            self.main_ui.Profile.setStyleSheet(f"background-color: {profile_button_color}; border-radius: {button_border_radius}; color: {profile_button_text_color}")
            self.main_ui.Home_Button.setStyleSheet(f"color: {logo_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px")
            self.main_ui.Version_button.setStyleSheet(f"color: {logo_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px")
            self.main_ui.frame.setStyleSheet(f"background-color: {logo_color}")
            self.main_ui.frame_2.setStyleSheet(f"background-color: {logo_color}")
            self.login_ui.titlebar.setStyleSheet(f"background-color: {title_bar_color};")
            self.login_ui.hide.setStyleSheet(f"color: {title_bar_button_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px;")
            self.login_ui.close.setStyleSheet(f"color: {title_bar_button_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px;")
            self.main_ui.start_game.setStyleSheet(f"background-color: {button_color}; border-radius: {button_border_radius}; color: {button_text_color}")
            self.main_ui.v189.setStyleSheet(f"background-color: {button_color}; border-radius: {button_border_radius}; color: {button_text_color}")
            self.main_ui.v1122.setStyleSheet(f"background-color: {button_color}; border-radius: {button_border_radius}; color: {button_text_color}")
            self.login_ui.Login_2.setStyleSheet(f"background-color: {button_color}; border-radius: {button_border_radius}; color: {button_text_color}")
            self.settings_ui.titlebar.setStyleSheet(f"background-color: {title_bar_color};")
            self.settings_ui.hide.setStyleSheet(f"color: {title_bar_button_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px;")
            self.settings_ui.close.setStyleSheet(f"color: {title_bar_button_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px;")
            self.settings_ui.Title.setStyleSheet(f"color: {logo_color}")
            self.settings_ui.Profile.setStyleSheet(f"background-color: {profile_button_color}; border-radius: {button_border_radius}; color: {profile_button_text_color}")
            self.settings_ui.Home_Button.setStyleSheet(f"color: {logo_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px")
            self.settings_ui.Version_button.setStyleSheet(f"color: {logo_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px")
            self.settings_ui.frame_3.setStyleSheet(f"background-color: {logo_color}")
            self.settings_ui.hide_window.setStyleSheet(f"background-color: {settings_item_background_color};\nborder-radius: 10px")
            self.settings_ui.theme.setStyleSheet(f"background-color: {settings_item_background_color};\nborder-radius: 10px")
            self.settings_ui.name.setStyleSheet(f"color: {settings_item_text_color}")
            self.settings_ui.name_2.setStyleSheet(f"color: {settings_item_text_color}")
            self.settings_ui.theme_button.setStyleSheet(f"background-color: {button_color}; border-radius: {button_border_radius}; color: {button_text_color}")
            self.settings_ui.hide_window_button.setStyleSheet(f"background-color: {button_color}; border-radius: {button_border_radius}; color: {button_text_color}")
            print("Theme applied successfully")
        except Exception as e:
            print(f"Failed to apply theme: {e}")
    
    def load_skin(self):
        global file_name
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Skin File", "", "JSON Files (*.json);;All Files (*)")
        if file_name:
            try:
                with open(file_name, 'r') as theme_file:
                    theme_data = json.load(theme_file)
                self.apply_theme(theme_data)
                self.savedata()
            except Exception as e:
                print(f"Failed to apply theme: {e}")

    def download_minecraft_version(self):
        global selected_version
        try:
            minecraft_launcher_lib.install.install_minecraft_version(selected_version, self.minecraft_directory)
        except Exception as e:
            print(f"Failed to install Minecraft version: {e}")

    def launch_minecraft_threaded(self):
        global starting
        if starting == False:
            threading.Thread(target=self.start_minecraft).start()

    def change_window_name(self):
        while True:
            minecraft_windows = gw.getWindowsWithTitle("Minecraft 1.8.9") or gw.getWindowsWithTitle("Minecraft 1.12.2")
            if minecraft_windows:
                minecraft_window = minecraft_windows[0]
                hwnd = minecraft_window._hWnd  # Get the window handle
                ctypes.windll.user32.SetWindowTextW(hwnd, "IT Client | 0.13")
                break
            time.sleep(1)

    def start_minecraft(self):
        global account, selected_version, starting
        if not account:
            self.main_ui.start_game.setText(f"LAUNCH {selected_version}")
            return
        
        self.main_ui.start_game.setText(f"INSTALLING {selected_version}")
        starting = True
        try:
            self.download_minecraft_version()
        except:
            print("CANNOT INSTALL MINECRAFT")

        self.main_ui.start_game.setText(f"LAUNCHING {selected_version}")
        threading.Thread(target=self.change_window_name).start()
        
        if hide_window_on_startup == "true":
            self.hide()

        options = {
            "username": account.get("username", "guest"),
            "uuid": account.get("id", ""),
            "token": account.get("access_token", "offline_mode"),
            "directory": self.minecraft_directory
        }

        minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(selected_version, self.minecraft_directory, options)
        try:
            process = subprocess.run(minecraft_command, cwd=self.minecraft_directory)
        except:
            print("CANNOT LAUNCH MINECRAFT")
            starting = False
            self.main_ui.start_game.setText(f"LAUNCH {selected_version}")
            self.show()
        
        starting = False
        self.main_ui.start_game.setText(f"LAUNCH {selected_version}")
        self.show()

app = QApplication(sys.argv)
window = Ui()
window.show()
app.exec_()
