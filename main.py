import os
import subprocess
import sys
import threading
import uuid
import json
import random
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import *
import requests
from mojang import Client
import minecraft_launcher_lib
import webbrowser

# ACTION CLIENT v0.13

CLIENT_ID = "33c92eaa-f60a-46b6-83b2-1d1713f0216b"
REDIRECT_URL = "http://localhost:8000/"
auth_code = None
state = None
code_verifier = None
access_token = None
version = "0.13"

print("ACTION CLIENT", version)
print("DO NOT SHARE YOUR ACCOUNTS FILE")

ACCOUNTS_FILE = "accounts.json"

class MinecraftLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Action Client")
        self.setFixedSize(800, 600)
        self.setStyleSheet("font-family: Montserrat; background-color: #2c2f38; color: white;")

        self.music_urls = {
            "Lumi Athena, jnhygs - SMOKE IT OFF": "https://dl2.mp3party.net/online/10791567.mp3",
            "Childish Gambino - Do Ya Like": "https://dl2.mp3party.net/online/10699100.mp3",
            "jnhygs, 9lives - JERK!": "https://su.muzmo.cc/get/music/20230816/jnhygs_-_JERK_prod_9lives_76577894.mp3",
            "skywave - a bird's last look": "https://muzdark.net/uploads/music/2024/04/A_bird_s_last_look_Macabre_plaza_best_part_only_slowed.mp3",
            "Baby Tate - Hey Mickey!": "https://dl2.mp3party.net/online/10726988.mp3",
            "Tyler, the Creator - RAH TAH TAH": "https://dl2.mp3party.net/online/11187685.mp3",
        }

        self.music_player = QMediaPlayer()
        self.music_player.setNotifyInterval(1000)
        self.music_player.mediaStatusChanged.connect(self.on_media_status_changed)

        self.current_track_index = 0
        self.current_song_name = list(self.music_urls.keys())[self.current_track_index]
        self.current_song_url = self.music_urls[self.current_song_name]
        self.play_music(self.current_song_url)

        self.title_label = QLabel("Action Radio")
        self.title_label.setStyleSheet("font-size: 24px; color: white; text-align: center; margin-top: 20px;")
        
        self.track_name_label = QLabel(self.current_song_name)
        self.track_name_label.setStyleSheet("font-size: 16px; color: white; text-align: center; margin-top: 10px;")

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.setValue(0)
        self.progress_slider.setStyleSheet("background-color: #4CAF50; height: 8px; border-radius: 5px;")

        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.track_name_label)
        layout.addWidget(self.progress_slider)

        # Main layout setup
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.stacked_widget = QStackedWidget()

        self.main_page = QWidget()
        self.add_account_page = QWidget()
        self.login_page = QWidget()

        self.init_main_page()
        self.init_add_account_page()
        self.init_login_page()

        self.stacked_widget.addWidget(self.main_page)
        self.stacked_widget.addWidget(self.add_account_page)
        self.stacked_widget.addWidget(self.login_page)

        self.setCentralWidget(self.stacked_widget)
        self.login_data = None
        self.accounts = []
        self.minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
        self.latest_version = minecraft_launcher_lib.utils.get_latest_version()["release"]

        self.load_accounts()

    def update_ui(self):
        """Update the UI with the current song and play the music."""
        self.music_label.setText(f"Action Radio: {self.current_song_name}")

    def log_output(self, message):
        self.output_area.append(message)

    def init_main_page(self):
        layout = QVBoxLayout()

        self.account_switcher = QComboBox()
        self.account_switcher.addItem("Select Account")
        self.account_switcher.setStyleSheet("padding: 10px; border-radius: 5px; font-size: 16px;")
        layout.addWidget(self.account_switcher)

        self.add_account_button = QPushButton("Add Account")
        self.add_account_button.setStyleSheet(self.button_style())
        self.add_account_button.clicked.connect(self.show_add_account_page)
        layout.addWidget(self.add_account_button)

        self.remove_account_button = QPushButton("Remove Account")
        self.remove_account_button.setStyleSheet(self.button_style())
        self.remove_account_button.clicked.connect(self.remove_account)
        layout.addWidget(self.remove_account_button)

        self.version_selector = QComboBox()
        installed_versions = minecraft_launcher_lib.utils.get_installed_versions(
            minecraft_launcher_lib.utils.get_minecraft_directory()
        )
        version_names = [version["id"] for version in installed_versions]
        self.version_selector.addItems(version_names)

        self.version_selector.setStyleSheet("padding: 10px; border-radius: 5px; font-size: 16px;")
        layout.addWidget(self.version_selector)

        self.launch_button = QPushButton("Launch Minecraft")
        self.launch_button.setStyleSheet(self.button_style())
        self.launch_button.clicked.connect(self.launch_minecraft_threaded)
        layout.addWidget(self.launch_button)

        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("font-size: 16px; color: #4CAF50;")
        layout.addWidget(self.status_label)

        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setStyleSheet("background: #3a3f47; border-radius: 8px; padding: 10px;")
        layout.addWidget(self.output_area)
        self.output_area.append("DO NOT SHARE YOUR ACCOUNTS FILE")

        self.music_label = QLabel(f"Now Playing: {self.current_song_name}")
        self.music_label.setStyleSheet("font-size: 16px; color: white; margin-top: 20px;")
        layout.addWidget(self.music_label)

        self.play_music_button = QPushButton("Play Action Radio")
        self.play_music_button.setStyleSheet(self.button_style())
        self.play_music_button.clicked.connect(self.toggle_play_pause)
        layout.addWidget(self.play_music_button)
        self.pause()

        self.prev_music_button = QPushButton("Previous Music")
        self.prev_music_button.setStyleSheet(self.button_style())
        self.prev_music_button.clicked.connect(self.previous_song)
        layout.addWidget(self.prev_music_button)

        self.next_music_button = QPushButton("Next Music")
        self.next_music_button.setStyleSheet(self.button_style())
        self.next_music_button.clicked.connect(self.next_song)
        layout.addWidget(self.next_music_button)

        self.main_page.setLayout(layout)

    def init_add_account_page(self):
        layout = QVBoxLayout()

        self.offline_username_input = QLineEdit()
        self.offline_username_input.setPlaceholderText("Enter username for Offline Mode")
        self.offline_username_input.setStyleSheet("padding: 10px; border-radius: 5px; font-size: 16px;")
        layout.addWidget(self.offline_username_input)

        self.offline_button = QPushButton("Play Offline")
        self.offline_button.setStyleSheet(self.button_style())
        self.offline_button.clicked.connect(self.play_offline)
        layout.addWidget(self.offline_button)

        self.microsoft_login_button = QPushButton("Login with Microsoft")
        self.microsoft_login_button.setStyleSheet(self.button_style())
        self.microsoft_login_button.clicked.connect(self.show_login_page)
        layout.addWidget(self.microsoft_login_button)

        self.back_button = QPushButton("Back")
        self.back_button.setStyleSheet(self.button_style())
        self.back_button.clicked.connect(self.show_main_page)
        layout.addWidget(self.back_button)

        self.add_account_page.setLayout(layout)

    def init_login_page(self):
        layout = QVBoxLayout()

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email Address")
        self.email_input.setStyleSheet("padding: 10px; border-radius: 5px; font-size: 16px;")
        layout.addWidget(self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("padding: 10px; border-radius: 5px; font-size: 16px;")
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("Log In")
        self.login_button.setStyleSheet(self.button_style())
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)

        self.back_button = QPushButton("Back")
        self.back_button.setStyleSheet(self.button_style())
        self.back_button.clicked.connect(self.show_add_account_page)
        layout.addWidget(self.back_button)

        self.login_page.setLayout(layout)

    def show_main_page(self):
        self.stacked_widget.setCurrentWidget(self.main_page)

    def show_add_account_page(self):
        self.stacked_widget.setCurrentWidget(self.add_account_page)

    def show_login_page(self):
        self.stacked_widget.setCurrentWidget(self.login_page)

    def button_style(self):
        return "padding: 10px; font-size: 18px; border-radius: 5px; background-color: #4CAF50; color: white; border: none;"

    def play_music(self, url):
        media = QMediaContent(QUrl(url))
        self.music_player.setMedia(media)
        self.music_player.play()

    def toggle_play_pause(self):
        if self.music_player.state() == QMediaPlayer.PlayingState:
            self.music_player.pause()
            self.play_music_button.setText("Play Action Radio")
        else:
            self.music_player.play()
            self.play_music_button.setText("Pause Action Radio")
    
    def pause(self):
        self.music_player.pause()
        self.play_music_button.setText("Play Action Radio")

    def next_song(self):
        self.current_track_index = (self.current_track_index + 1) % len(self.music_urls)
        self.current_song_name = list(self.music_urls.keys())[self.current_track_index]
        self.current_song_url = self.music_urls[self.current_song_name]
        self.update_ui()
        self.play_music_button.setText("Pause Action Radio")

    def previous_song(self):
        self.current_track_index = (self.current_track_index - 1) % len(self.music_urls)
        self.current_song_name = list(self.music_urls.keys())[self.current_track_index]
        self.current_song_url = self.music_urls[self.current_song_name]
        self.update_ui()
        self.play_music_button.setText("Pause Action Radio")

    def update_ui(self):
        self.music_label.setText(self.current_song_name)
        self.play_music(self.current_song_url)

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.next_song()

    def on_position_changed(self, position):
        duration = self.music_player.duration()
        if duration > 0:
            position_percentage = (position / duration) * 100
            self.progress_slider.setValue(position_percentage)
    
    def play_offline(self):
        username = self.offline_username_input.text()
        if username:
            account = {"access_token": "offline_mode", "username": username, "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, username))}
            self.accounts.append(account)
            self.save_accounts()
            self.show_main_page()
            self.output_area.append(f"Offline account added: {username}")
        else:
            self.output_area.append("Error: Username cannot be empty for offline mode.")

    def login(self):
        username = self.email_input.text()
        password = self.password_input.text()

        try:
            session = requests.Session()
            client = Client(username, password, session=session)

            profile_response = client.request("get", "https://api.minecraftservices.com/minecraft/profile")
            profile_data = profile_response.json()

            self.log_output("Successfully logged with Microsoft/Mojang")

            self.login_data = {
                "name": profile_data['name'],
                "id": profile_data['id'],
                "access_token": client.bearer_token,
            }

            account = {"access_token": client.bearer_token, "username": self.login_data["name"], "id": profile_data['id']}
            print(account)
            self.accounts.append(account)
            self.save_accounts()
            self.status_label.setText(f"Logged in as {self.login_data['name']}")
            self.show_main_page()
        except Exception as e:
            self.status_label.setText(f"Login failed: {e}")
            print(f"Error during login: {e}")
    
    def perform_microsoft_login(self):
        try:
            login_data = minecraft_launcher_lib.account.complete_microsoft_login()
            account = {"type": "microsoft", "username": login_data["name"], "access_token": login_data["access_token"]}
            self.accounts.append(account)
            self.save_accounts()
            self.show_main_page()
            self.output_area.append(f"Microsoft account added: {login_data['name']}")
        except Exception as e:
            self.output_area.append(f"Microsoft login failed: {e}")

    def remove_account(self):
        selected_account = self.account_switcher.currentText()

        if selected_account == "Select Account":
            return

        self.accounts = [account for account in self.accounts if account != selected_account]
        
        self.save_accounts()

        self.account_switcher.clear()
        self.account_switcher.addItem("Select Account")
        self.account_switcher.addItems(self.accounts)

        self.status_label.setText(f"Account {selected_account} removed")

    def save_accounts(self):
        with open(ACCOUNTS_FILE, 'w') as f:
            json.dump(self.accounts, f)
        self.load_accounts()

    def load_accounts(self):
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, 'r') as f:
                self.accounts = json.load(f)
                print(self.accounts)
                self.account_switcher.clear()
                self.account_switcher.addItem("Select Account")
                
                for account in self.accounts:
                    if isinstance(account, dict) and "username" in account:
                        self.account_switcher.addItem(account["username"])
                    else:
                        print("Error: Invalid account data format")

    def account_selected(self):
        selected_account = self.account_switcher.currentText()
        if selected_account == "Select Account":
            return

        for account in self.accounts:
            if account == selected_account:
                self.login_data = {"name": account, "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, account)), "access_token": "offline_mode"}
                self.status_label.setText(f"Switched to {account}")
                break

    def launch_minecraft_threaded(self):
        threading.Thread(target=self.launch_minecraft).start()

    def launch_minecraft(self):
        selected_index = self.account_switcher.currentIndex() - 1
        if selected_index < 0 or selected_index >= len(self.accounts):
            self.output_area.append("Error: No valid account selected.")
            return

        selected_account = self.accounts[selected_index]
        selected_version = self.version_selector.currentText()

        try:
            self.output_area.append(f"Starting game...")
            options = {
                "username": selected_account["username"],
                "uuid": selected_account.get("id", ""),
                "token": selected_account.get("access_token", ""),
                "directory": self.minecraft_directory
            }

            print(options)

            minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(selected_version, self.minecraft_directory, options)
            subprocess.run(minecraft_command, cwd=self.minecraft_directory)
            self.output_area.append(f"Game successfully stopped")
            self.status_label.setText("Status: Ready")
        except Exception as e:
            self.output_area.append(f"Failed to launch Minecraft: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = MinecraftLauncher()
    launcher.account_switcher.currentIndexChanged.connect(launcher.account_selected)
    launcher.show()
    sys.exit(app.exec_())
