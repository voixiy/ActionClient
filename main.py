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
from msal import PublicClientApplication
import minecraft_launcher_lib
import webbrowser
import pygetwindow as gw
import time
import ctypes
from pypresence import Presence
from mojang import *

client_id = '33c92eaa-f60a-46b6-83b2-1d1713f0216b'
TENANT_ID = '6f730e5c-e17b-4434-8d56-f3faa97bfda7'
authority = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/.default"]
selected_version = "1.8.9"
loggedin = False
account = {}
CLIENT_ID = "1318959471338459198"
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
    "version": "",
    "playlist": 1
}
starting = False
notplayed = False
hide_window_on_startup = "true"
file_name = ""
playlist = 1

try:
    rpc = Presence(CLIENT_ID)
    rpc.connect()

    rpc.update(
        details="Playing Minecraft",
        large_image="icon",
        large_text="IT Client",
        small_image="code",
        small_text="Playing Minecraft",
        start=time.time()
    )
except:
    print("Could not find discord installed and running on this machine")

class Ui(QMainWindow):
    def __init__(self):
        self.minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
        super(Ui, self).__init__()
        self.setWindowTitle("IT Client")
        self.setFixedSize(765, 443)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.init_ui()

    def init_ui(self):
        global selected_version, account, hide_window_on_startup, file_name, playlist
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        self.player = QMediaPlayer()
        self.player.stateChanged.connect(self.update_button_icon)
        self.player.mediaStatusChanged.connect(self.check_media_status)

        self.songs = {
            'jnhygs, 9lives - JERK!': 'https://rildi.sunproxy.net/file/T2haZld6QlROcWNYcU93VmhhNnJmTytIUDUzSlUwZ0xEU0s3bEQ2dmtPcEZvYllwK0ZHOHd0aUoySHpHdlZHTU83amxJZzNaV09wK3Z6YUFhT1Q4dVQ5eTZjUlc2ZUhxMEdYOWVUR1lWYnc9/jnhygs_-_JERK_prod._9lives_(Hydr0.org).mp3',
            'Baby Tate - Hey Mickey': 'https://rildi.sunproxy.net/file/T2haZld6QlROcWNYcU93VmhhNnJmSHJzTkYra00rM3BxRXZtaDBnR1JHQ05BTWI3ZDVJQ2VOZ1lndVMwZjhRNmh3S2lKZEVwM2F5b2IvdUp5Y2diK0VodytLVGY2OFIwY0RBeGxZL2NacDQ9/Baby_Tate_-_Hey_Mickey_prod._by_deadhead_(Hydr0.org).mp3',
            'VANO 3000 - Running Away': 'https://rildi.sunproxy.net/file/T2haZld6QlROcWNYcU93VmhhNnJmSHJzTkYra00rM3BxRXZtaDBnR1JHQ05BTWI3ZDVJQ2VOZ1lndVMwZjhRNnNaMXpxK2sxOVlqQnNZK0dFZ2l5aHI1ZzB1UEhqNVZhZnBNbE5pRGJoRE09/VANO_3000_-_Running_Away_Vocal_Remix_(Hydr0.org).mp3',
            'Oderati, 6arelyhuman - GMFU': 'https://dl2.mp3party.net/online/10870802.mp3',
            'KSI - Sick of it': "https://dl2.mp3party.net/online/11171382.mp3",
            'Eminem - Godzilla': 'https://dl2.mp3party.net/online/9201529.mp3',
            'Ghostemane - Mercury': 'https://dl2.mp3party.net/online/8571364.mp3',
            'Tyler, The Creator - Rah Tah Tah': 'https://dl2.mp3party.net/online/11187685.mp3',
            'alt! - RAHHHH': 'https://mp3uk.net/mp3/files/alt-rahhhh-mp3.mp3'
        }

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

        self.offline_ui = QMainWindow()
        uic.loadUi('ui\\Offline.ui', self.offline_ui)
        self.stack.addWidget(self.offline_ui)

        self.microsoft_ui = QMainWindow()
        uic.loadUi('ui\\Microsoft.ui', self.microsoft_ui)
        self.stack.addWidget(self.microsoft_ui)

        self.playlists_ui = QMainWindow()
        uic.loadUi('ui\\Playlists.ui', self.playlists_ui)
        self.stack.addWidget(self.playlists_ui)

        if os.path.exists("json\\config.json"):
            with open("json\\config.json", 'r') as f:
                config = json.load(f)
            account = config.get("account", {})
            settings_config = config.get("settings", {})
            if account != {}:
                username = account.get("username")
                self.main_ui.Profile.setText(f"Hello, {username}")
                self.settings_ui.Profile.setText(f"Hello, {username}")
                try: 
                    head_image_url = self.get_player_head_image(username)
                    pixmap = QPixmap()
                    pixmap.loadFromData(requests.get(head_image_url).content)
                    icon = QIcon(pixmap)
                    self.main_ui.Profile.setIcon(icon)
                    self.settings_ui.Profile.setIcon(icon)
                except:
                    print("No connection")
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
            if config.get("playlist", 1) == 1:
                self.songs = {
                    'jnhygs, 9lives - JERK!': 'https://rildi.sunproxy.net/file/T2haZld6QlROcWNYcU93VmhhNnJmTytIUDUzSlUwZ0xEU0s3bEQ2dmtPcEZvYllwK0ZHOHd0aUoySHpHdlZHTU83amxJZzNaV09wK3Z6YUFhT1Q4dVQ5eTZjUlc2ZUhxMEdYOWVUR1lWYnc9/jnhygs_-_JERK_prod._9lives_(Hydr0.org).mp3',
                    'Baby Tate - Hey Mickey': 'https://rildi.sunproxy.net/file/T2haZld6QlROcWNYcU93VmhhNnJmSHJzTkYra00rM3BxRXZtaDBnR1JHQ05BTWI3ZDVJQ2VOZ1lndVMwZjhRNmh3S2lKZEVwM2F5b2IvdUp5Y2diK0VodytLVGY2OFIwY0RBeGxZL2NacDQ9/Baby_Tate_-_Hey_Mickey_prod._by_deadhead_(Hydr0.org).mp3',
                    'VANO 3000 - Running Away': 'https://rildi.sunproxy.net/file/T2haZld6QlROcWNYcU93VmhhNnJmSHJzTkYra00rM3BxRXZtaDBnR1JHQ05BTWI3ZDVJQ2VOZ1lndVMwZjhRNnNaMXpxK2sxOVlqQnNZK0dFZ2l5aHI1ZzB1UEhqNVZhZnBNbE5pRGJoRE09/VANO_3000_-_Running_Away_Vocal_Remix_(Hydr0.org).mp3',
                    'Oderati, 6arelyhuman - GMFU': 'https://dl2.mp3party.net/online/10870802.mp3',
                    'KSI - Sick of it': "https://dl2.mp3party.net/online/11171382.mp3",
                    'Eminem - Godzilla': 'https://dl2.mp3party.net/online/9201529.mp3',
                    'Ghostemane - Mercury': 'https://dl2.mp3party.net/online/8571364.mp3',
                    'Tyler, The Creator - Rah Tah Tah': 'https://dl2.mp3party.net/online/11187685.mp3',
                    'alt! - RAHHHH': 'https://mp3uk.net/mp3/files/alt-rahhhh-mp3.mp3'
                }
            elif config.get("playlist", 1) == 2:
                self.songs = {
                    'MF DOOM - Doomsday': 'https://dl2.mp3party.net/online/8739037.mp3',
                    'narpy - so far away': 'https://ia801608.us.archive.org/27/items/soundcloud-1341492589/1341492589.mp3',
                    'narpy - cherry blossoms': 'https://ia801608.us.archive.org/27/items/soundcloud-1280029051/1280029051.mp3',
                    'LAKEY INSPIRED - Blue Boi': 'https://happysoulmusic.com/wp-content/grand-media/audio/Lakey-Inspired-Blue-Boi.mp3',
                    'Domknowz - Lofi': "https://dl2.mp3party.net/online/10299262.mp3",
                    'Closed on saturday - animal crossing new horizons lofi': 'https://rildi.sunproxy.net/file/bWZVZG9jcU9tREpWU3hRSE5GZmFCaHJXa1F4UXhtV3MvY0pvWjM0SlpDeWFsVjZBeUVOMGFsK3JNbGRHWitVb0F3ZGIxRXphWVpwdUwzRm92TW1LeFpzMEFneWpEdzVZalFadVVrbDM4elE9/Unknown_-_animal_crossing_new_horizons_lofi_(Hydr0.org).mp3'
                }

        self.main_ui.findChild(QPushButton, 'Profile').clicked.connect(self.switch_to_login)
        self.settings_ui.findChild(QPushButton, 'Profile').clicked.connect(self.switch_to_login)
        self.login_ui.findChild(QPushButton, 'back').clicked.connect(self.switch_to_main)
        self.offline_ui.findChild(QPushButton, 'back').clicked.connect(self.switch_to_main)
        self.microsoft_ui.findChild(QPushButton, 'back').clicked.connect(self.switch_to_main)
        self.playlists_ui.findChild(QPushButton, 'back').clicked.connect(self.switch_to_main)
        self.main_ui.findChild(QPushButton, 'start_game').clicked.connect(self.launch_minecraft_threaded)
        self.login_ui.findChild(QPushButton, 'offline').clicked.connect(self.switch_to_offline)
        self.login_ui.findChild(QPushButton, 'microsoft').clicked.connect(self.switch_to_microsoft)
        self.login_ui.findChild(QPushButton, 'microsoft').clicked.connect(self.play_with_microsoft_threaded)
        self.offline_ui.findChild(QPushButton, 'Login_2').clicked.connect(self.play_offline)
        self.main_ui.findChild(QPushButton, 'v189').clicked.connect(self.switch_to_189)
        self.main_ui.findChild(QPushButton, 'v1122').clicked.connect(self.switch_to_1122)
        self.offline_ui.username.max_length = 20
        self.offline_ui.username.textChanged.connect(self.enforce_max_length)
        self.main_ui.frame_2.hide()
        self.main_ui.findChild(QPushButton, 'close').clicked.connect(self.close)
        self.main_ui.hide.clicked.connect(self.window().showMinimized)
        self.login_ui.findChild(QPushButton, 'close').clicked.connect(self.close)
        self.login_ui.hide.clicked.connect(self.window().showMinimized)
        self.settings_ui.findChild(QPushButton, 'close').clicked.connect(self.close)
        self.settings_ui.hide.clicked.connect(self.window().showMinimized)
        self.offline_ui.findChild(QPushButton, 'close').clicked.connect(self.close)
        self.offline_ui.hide.clicked.connect(self.window().showMinimized)
        self.microsoft_ui.findChild(QPushButton, 'close').clicked.connect(self.close)
        self.microsoft_ui.hide.clicked.connect(self.window().showMinimized)
        self.playlists_ui.findChild(QPushButton, 'close').clicked.connect(self.close)
        self.playlists_ui.hide.clicked.connect(self.window().showMinimized)
        self.main_ui.Versions.hide()
        self.main_ui.Settings_button.clicked.connect(self.switch_to_settings)
        self.settings_ui.Home_Button_2.clicked.connect(self.switch_to_main_home)
        self.settings_ui.Version_button.clicked.connect(self.switch_to_main_versions)
        self.settings_ui.theme_button.clicked.connect(self.load_skin)
        self.settings_ui.hide_window_button.clicked.connect(self.hide_window)
        self.main_ui.skip.clicked.connect(self.play_random_song)
        self.main_ui.previous.clicked.connect(self.play_random_song)
        self.main_ui.play.setIcon(QIcon("ui/resources/play.png"))
        self.main_ui.skip.setIcon(QIcon("ui/resources/end.png"))
        self.main_ui.previous.setIcon(QIcon("ui/resources/skip_to_start.png"))
        self.main_ui.play.clicked.connect(self.toggle_play_pause)
        self.settings_ui.skip.clicked.connect(self.play_random_song)
        self.settings_ui.previous.clicked.connect(self.play_random_song)
        self.settings_ui.play.setIcon(QIcon("ui/resources/play.png"))
        self.settings_ui.skip.setIcon(QIcon("ui/resources/end.png"))
        self.settings_ui.previous.setIcon(QIcon("ui/resources/skip_to_start.png"))
        self.settings_ui.play.clicked.connect(self.toggle_play_pause)
        self.main_ui.Profile.setIcon(QIcon("ui/resources/guest.png"))
        self.settings_ui.Profile.setIcon(QIcon("ui/resources/guest.png"))
        self.main_ui.background.icon = QPixmap("ui/resources/background.png")

        self.shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        self.shortcut.activated.connect(self.toggle_play_pause)

        self.shortcut2 = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.shortcut2.activated.connect(self.play_random_song)

        self.playlists_ui.aggressive.clicked.connect(self.change_playlist_1)
        self.playlists_ui.chill.clicked.connect(self.change_playlist_2)

        self.main_ui.playlists.clicked.connect(self.switch_to_playlists)
        self.settings_ui.playlists.clicked.connect(self.switch_to_playlists)

    def play_random_song(self):
        global notplayed
        song_name, song_url = random.choice(list(self.songs.items()))
        url = QUrl(song_url)
        content = QMediaContent(url)
        self.player.setMedia(content)
        self.player.play()
        self.main_ui.songname.setText(song_name)
        self.settings_ui.songname.setText(song_name)
        notplayed = True
    
    def change_playlist_1(self):
        global playlist
        playlist = 1
        self.songs = {
            'jnhygs, 9lives - JERK!': 'https://rildi.sunproxy.net/file/T2haZld6QlROcWNYcU93VmhhNnJmTytIUDUzSlUwZ0xEU0s3bEQ2dmtPcEZvYllwK0ZHOHd0aUoySHpHdlZHTU83amxJZzNaV09wK3Z6YUFhT1Q4dVQ5eTZjUlc2ZUhxMEdYOWVUR1lWYnc9/jnhygs_-_JERK_prod._9lives_(Hydr0.org).mp3',
            'Baby Tate - Hey Mickey': 'https://rildi.sunproxy.net/file/T2haZld6QlROcWNYcU93VmhhNnJmSHJzTkYra00rM3BxRXZtaDBnR1JHQ05BTWI3ZDVJQ2VOZ1lndVMwZjhRNmh3S2lKZEVwM2F5b2IvdUp5Y2diK0VodytLVGY2OFIwY0RBeGxZL2NacDQ9/Baby_Tate_-_Hey_Mickey_prod._by_deadhead_(Hydr0.org).mp3',
            'VANO 3000 - Running Away': 'https://rildi.sunproxy.net/file/T2haZld6QlROcWNYcU93VmhhNnJmSHJzTkYra00rM3BxRXZtaDBnR1JHQ05BTWI3ZDVJQ2VOZ1lndVMwZjhRNnNaMXpxK2sxOVlqQnNZK0dFZ2l5aHI1ZzB1UEhqNVZhZnBNbE5pRGJoRE09/VANO_3000_-_Running_Away_Vocal_Remix_(Hydr0.org).mp3',
            'Oderati, 6arelyhuman - GMFU': 'https://dl2.mp3party.net/online/10870802.mp3',
            'KSI - Sick of it': 'https://dl2.mp3party.net/online/11171382.mp3',
            'Eminem - Godzilla': 'https://dl2.mp3party.net/online/9201529.mp3',
            'Ghostemane - Mercury': 'https://dl2.mp3party.net/online/8571364.mp3',
            'Tyler, The Creator - Rah Tah Tah': 'https://dl2.mp3party.net/online/11187685.mp3',
            'alt! - RAHHHH': 'https://mp3uk.net/mp3/files/alt-rahhhh-mp3.mp3'
        }
        self.switch_to_main()
        self.savedata()
    
    def change_playlist_2(self):
        global playlist
        playlist = 2
        self.songs = {
            'MF DOOM - Doomsday': 'https://dl2.mp3party.net/online/8739037.mp3',
            'narpy - so far away': 'https://ia801608.us.archive.org/27/items/soundcloud-1341492589/1341492589.mp3',
            'narpy - cherry blossoms': 'https://ia801608.us.archive.org/27/items/soundcloud-1280029051/1280029051.mp3',
            'LAKEY INSPIRED - Blue Boi': 'https://happysoulmusic.com/wp-content/grand-media/audio/Lakey-Inspired-Blue-Boi.mp3',
            'Domknowz - Lofi': "https://dl2.mp3party.net/online/10299262.mp3",
            'Closed on saturday - animal crossing new horizons lofi': 'https://rildi.sunproxy.net/file/bWZVZG9jcU9tREpWU3hRSE5GZmFCaHJXa1F4UXhtV3MvY0pvWjM0SlpDeWFsVjZBeUVOMGFsK3JNbGRHWitVb0F3ZGIxRXphWVpwdUwzRm92TW1LeFpzMEFneWpEdzVZalFadVVrbDM4elE9/Unknown_-_animal_crossing_new_horizons_lofi_(Hydr0.org).mp3'
        }
        self.switch_to_main()
        self.savedata()

    def toggle_play_pause(self):
        global notplayed
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()
        if notplayed == False:
            self.play_random_song()

    def update_button_icon(self, state):
        if state == QMediaPlayer.PlayingState:
            self.main_ui.play.setIcon(QIcon("ui/resources/pause.png"))
            self.settings_ui.play.setIcon(QIcon("ui/resources/pause.png"))
        else:
            self.main_ui.play.setIcon(QIcon("ui/resources/play.png"))
            self.settings_ui.play.setIcon(QIcon("ui/resources/play.png"))

    def check_media_status(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.play_random_song()

    def hide_window(self):
        if hide_window_on_startup == "true":
            self.enable_disable_hide_window()
            self.settings_ui.hide_window_button.setText("Enabled")
        else:
            self.enable_disable_hide_window()
            self.settings_ui.hide_window_button.setText("Disabled")

    def enforce_max_length(self):
        text = self.offline_ui.username.toPlainText()
        if len(text) > self.offline_ui.username.max_length:
            self.offline_ui.username.setPlainText(text[:self.offline_ui.username.max_length])

    def enable_disable_hide_window(self):
        global hide_window_on_startup
        self.savedata()
        if hide_window_on_startup == "true":
            hide_window_on_startup = "false"
        else:
            hide_window_on_startup = "true"

    def get_player_head_image(self, username):
        response = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{username}")
        if response.status_code == 200:
            player_data = response.json()
            uuid = player_data['id']
            head_image_url = f"https://crafatar.com/renders/head/{uuid}?size=100&overlay"
            return head_image_url
        else:
            return None

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            event.ignore()
        else:
            super(Ui, self).keyPressEvent(event)

    def switch_to_login(self):
        self.stack.setCurrentWidget(self.login_ui)

    def switch_to_playlists(self):
        self.stack.setCurrentWidget(self.playlists_ui)

    def switch_to_settings(self):
        self.stack.setCurrentWidget(self.settings_ui)

    def switch_to_offline(self):
        self.stack.setCurrentWidget(self.offline_ui)

    def switch_to_microsoft(self):
        self.stack.setCurrentWidget(self.microsoft_ui)

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

    def play_with_microsoft(self):
        global account, data
        app = PublicClientApplication(client_id, authority=authority)

        device_flow = app.initiate_device_flow(scopes=["User.Read"])
        if "user_code" not in device_flow:
            raise ValueError("Failed to create device flow. Check app registration.")

        print(f"Go to {device_flow['verification_uri']} and enter the code: {device_flow['user_code']}")
        self.microsoft_ui.title_2.setText(f"Code: {device_flow['user_code']}")
        webbrowser.open(device_flow['verification_uri'])

        result = app.acquire_token_by_device_flow(device_flow)

        if "access_token" in result:
            access_token = result["access_token"]
            client = Client(bearer_token=access_token)
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            try:
                profile = client.get_profile()
                account = {"access_token": access_token, "username": profile.name, "id": profile.id}
                head_image_url = self.get_player_head_image(profile.name)
                pixmap = QPixmap()
                pixmap.loadFromData(requests.get(head_image_url).content)
                icon = QIcon(pixmap)
                self.main_ui.Profile.setIcon(icon)
                self.settings_ui.Profile.setIcon(icon)
                self.savedata()
            except:
                print("Can't get profile")
            self.switch_to_main()
        else:
            print("Authentication failed:", result.get("error_description"))

    def savedata(self):
        global selected_version, account, hide_window_on_startup, file_name, playlist
        print("SAVING CONFIG")
        data = {
            "account": account,
            "settings": {
                "hide_window_when_startup": hide_window_on_startup,
                "theme": file_name
            },
            "version": selected_version,
            "playlist": playlist
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
        username = self.offline_ui.findChild(QTextEdit, 'username').toPlainText()
        if username:
            account = {"access_token": "offline_mode", "username": username, "id": str(uuid.uuid3(uuid.NAMESPACE_DNS, username))}
            head_image_url = self.get_player_head_image(username)
            pixmap = QPixmap()
            pixmap.loadFromData(requests.get(head_image_url).content)
            icon = QIcon(pixmap)
            self.main_ui.Profile.setIcon(icon)
            self.settings_ui.Profile.setIcon(icon)
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
            logo_color = theme_data.get("text_color", "white")
            frame_color = theme_data.get("frame_color", "rgb(59, 59, 59)")
            profile_button_color = theme_data.get("profile_button_color", "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgb(130, 130, 130), stop:1 rgb(171, 171, 171))")
            profile_button_text_color = theme_data.get("profile_button_text_color", "white")
            settings_item_background_color = theme_data.get("settings_item_background_color", "rgb(36, 36, 36)")
            settings_item_text_color = theme_data.get("settings_item_text_color", "white")

            self.main_ui.setStyleSheet(f"background-color: {background_color};")
            self.login_ui.setStyleSheet(f"background-color: {background_color};")
            self.settings_ui.setStyleSheet(f"background-color: {background_color};")
            self.offline_ui.setStyleSheet(f"background-color: {background_color};")
            self.microsoft_ui.setStyleSheet(f"background-color: {background_color};")
            self.playlists_ui.setStyleSheet(f"background-color: {background_color};")
            self.main_ui.titlebar.setStyleSheet(f"background-color: {title_bar_color};")
            self.main_ui.hide.setStyleSheet(f"color: {title_bar_button_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px;")
            self.main_ui.close.setStyleSheet(f"color: {title_bar_button_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px;")
            self.main_ui.Title.setStyleSheet(f"color: {logo_color}")
            self.microsoft_ui.title.setStyleSheet(f"color: {logo_color}")
            self.offline_ui.title.setStyleSheet(f"color: {logo_color}")
            self.main_ui.Profile.setStyleSheet(f"background-color: {profile_button_color}; border-radius: {button_border_radius}; color: {profile_button_text_color}")
            self.main_ui.Home_Button.setStyleSheet(f"color: {logo_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px")
            self.main_ui.Version_button.setStyleSheet(f"color: {logo_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px")
            self.main_ui.frame.setStyleSheet(f"background-color: {logo_color}")
            self.main_ui.frame_2.setStyleSheet(f"background-color: {logo_color}")
            self.login_ui.titlebar.setStyleSheet(f"background-color: {title_bar_color};")
            self.login_ui.hide.setStyleSheet(f"color: {title_bar_button_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px;")
            self.login_ui.close.setStyleSheet(f"color: {title_bar_button_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px;")
            self.offline_ui.titlebar.setStyleSheet(f"background-color: {title_bar_color};")
            self.offline_ui.hide.setStyleSheet(f"color: {title_bar_button_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px;")
            self.offline_ui.close.setStyleSheet(f"color: {title_bar_button_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px;")
            self.microsoft_ui.titlebar.setStyleSheet(f"background-color: {title_bar_color};")
            self.microsoft_ui.hide.setStyleSheet(f"color: {title_bar_button_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px;")
            self.microsoft_ui.close.setStyleSheet(f"color: {title_bar_button_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px;")
            self.playlists_ui.titlebar.setStyleSheet(f"background-color: {title_bar_color};")
            self.playlists_ui.hide.setStyleSheet(f"color: {title_bar_button_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px;")
            self.playlists_ui.close.setStyleSheet(f"color: {title_bar_button_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px;")
            self.main_ui.start_game.setStyleSheet(f"background-color: {button_color}; border-radius: {button_border_radius}; color: {button_text_color}")
            self.login_ui.microsoft.setStyleSheet(f"background-color: {button_color}; border-radius: {button_border_radius}; color: {button_text_color}")
            self.login_ui.offline.setStyleSheet(f"background-color: {button_color}; border-radius: {button_border_radius}; color: {button_text_color}")
            self.main_ui.v189.setStyleSheet(f"background-color: {button_color}; border-radius: {button_border_radius}; color: {button_text_color}")
            self.main_ui.v1122.setStyleSheet(f"background-color: {button_color}; border-radius: {button_border_radius}; color: {button_text_color}")
            self.offline_ui.Login_2.setStyleSheet(f"background-color: {button_color}; border-radius: {button_border_radius}; color: {button_text_color}")
            self.settings_ui.titlebar.setStyleSheet(f"background-color: {title_bar_color};")
            self.settings_ui.hide.setStyleSheet(f"color: {title_bar_button_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px;")
            self.settings_ui.close.setStyleSheet(f"color: {title_bar_button_color}; border-top-left-radius : 10px;border-top-right-radius : 10px;border-bottom-left-radius:10px;border-bottom-right-radius : 10px;")
            self.settings_ui.Title.setStyleSheet(f"color: {logo_color}")
            self.settings_ui.songname.setStyleSheet(f"color: {logo_color}")
            self.main_ui.songname.setStyleSheet(f"color: {logo_color}")
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
            self.main_ui.frame_3.setStyleSheet(f"background-color: {frame_color}; border-radius: 10px")
            self.main_ui.label.setStyleSheet(f"color: {logo_color}")
            self.playlists_ui.label.setStyleSheet(f"color: {logo_color}")
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
    
    def play_with_microsoft_threaded(self):
        threading.Thread(target=self.play_with_microsoft).start()

    def change_window_name(self):
        while True:
            minecraft_windows = gw.getWindowsWithTitle("Minecraft 1.8.9") or gw.getWindowsWithTitle("Minecraft 1.12.2")
            if minecraft_windows:
                minecraft_window = minecraft_windows[0]
                hwnd = minecraft_window._hWndSYTWHUYH2YFU
                ctypes.windll.user32.SetWindowTextW(hwnd, "IT Client | v0.3-alpha")
                break
            time.sleep(1)

    def start_minecraft(self):
        global account, selected_version, starting, hide_window_on_startup
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