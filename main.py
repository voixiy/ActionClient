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

selected_version = "1.8.9"
loggedin = False
account = {}
data = {
    "account": {
        "access_token": "",
        "username": "",
        "id": ""
    },
    "version": ""
}
starting = False

class Ui(QMainWindow):
    def __init__(self):
        self.minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
        super(Ui, self).__init__()
        self.setWindowTitle("IT Client")
        self.setFixedSize(765, 443)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.init_ui()

    def init_ui(self):
        global selected_version, account
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        self.main_ui = QMainWindow()
        uic.loadUi('ui\\Design.ui', self.main_ui)
        self.stack.addWidget(self.main_ui)

        self.main_ui.start_game.setText(f"LAUNCH {selected_version}")

        self.login_ui = QMainWindow()
        uic.loadUi('ui\\Login.ui', self.login_ui)
        self.stack.addWidget(self.login_ui)

        if os.path.exists("json\\config.json"):
            with open("json\\config.json", 'r') as f:
                config = json.load(f)
            account = config.get("account")
            if account != {}:
                username = account.get("username")
                self.main_ui.Profile.setText(f"Hello, {username}")
            selected_version = config.get("version")
            self.main_ui.start_game.setText(f"LAUNCH {selected_version}")

        if os.path.exists("customization\\default.json"):
            with open("customization\\default.json", 'r') as f:
                config = json.load(f)
            self.apply_theme(config)

        self.main_ui.findChild(QPushButton, 'Profile').clicked.connect(self.switch_to_login)
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
        self.main_ui.Versions.hide()

    def enforce_max_length(self):
        text = self.login_ui.username.toPlainText()
        if len(text) > self.login_ui.username.max_length:
            self.login_ui.username.setPlainText(text[:self.login_ui.username.max_length])

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            event.ignore()
        else:
            super(Ui, self).keyPressEvent(event)

    def switch_to_login(self):
        self.stack.setCurrentWidget(self.login_ui)

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

    def savedata(self):
        global selected_version, account
        print("SAVING CONFIG")
        data = {
            "account": account,
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

            self.main_ui.setStyleSheet(f"background-color: {background_color};")
            self.login_ui.setStyleSheet(f"background-color: {background_color};")
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
            self.login_ui.Login_2.setStyleSheet(f"background-color: {button_color}; border-radius: {button_border_radius}; color: {button_text_color}")
            print("Theme applied successfully")
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

        options = {
            "username": account.get("username", "guest"),
            "uuid": account.get("id", ""),
            "token": account.get("access_token", "offline_mode"),
            "directory": self.minecraft_directory
        }

        minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(selected_version, self.minecraft_directory, options)
        try:
            process = subprocess.run(minecraft_command, cwd=self.minecraft_directory)
            self.hide()
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
