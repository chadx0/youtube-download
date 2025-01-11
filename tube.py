import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QProgressBar, QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap, QImage, QIcon, QColor
from PyQt5.QtCore import Qt, QRect, QThread, pyqtSignal, pyqtSlot
from pytube import YouTube
import os
import urllib.request
import webbrowser

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class VideoInfoWorker(QThread):
    finished = pyqtSignal(str, bytes)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            yt = YouTube(self.url)
            title = yt.title
            thumbnail_url = 'https://i.ytimg.com/vi/{}/maxresdefault.jpg'.format(yt.video_id)
            thumbnail_data = urllib.request.urlopen(thumbnail_url).read()
            self.finished.emit(title, thumbnail_data)
        except Exception as e:
            print(e)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Fast Tube")
        self.setFixedSize(1000, 800)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        url_layout = QHBoxLayout()
        url_label = QLabel("Video URL:")
        url_layout.addWidget(url_label)
        self.url_input = QLineEdit()
        url_layout.addWidget(self.url_input)
        fetch_button = QPushButton("Fetch Info")
        fetch_button.clicked.connect(self.fetch_info)
        url_layout.addWidget(fetch_button)
        main_layout.addLayout(url_layout)

        self.video_info_label = QLabel()
        main_layout.addWidget(self.video_info_label)

        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.thumbnail_label)

    

        save_layout = QHBoxLayout()
        save_label = QLabel("Save Location:")
        save_layout.addWidget(save_label)
        self.save_path_input = QLineEdit(os.path.expanduser("~\Desktop"))
        save_layout.addWidget(self.save_path_input)
        save_button = QPushButton("Select")
        save_button.clicked.connect(self.select_save_location)
        save_layout.addWidget(save_button)
        main_layout.addLayout(save_layout)

        self.video_quality_combo = QComboBox()
        self.video_quality_combo.addItem("Choose Video Quality...")
        self.video_quality_combo.setEnabled(False)
        main_layout.addWidget(self.video_quality_combo)

        self.audio_quality_combo = QComboBox()
        self.audio_quality_combo.addItem("Choose Audio Quality...")
        self.audio_quality_combo.setEnabled(False)
        main_layout.addWidget(self.audio_quality_combo)

        self.download_video_button = QPushButton("Download Video")
        self.download_video_button.clicked.connect(self.download_video)
        self.download_video_button.setEnabled(False)
        main_layout.addWidget(self.download_video_button)

        self.download_audio_button = QPushButton("Download Audio")
        self.download_audio_button.clicked.connect(self.download_audio)
        self.download_audio_button.setEnabled(False)
        main_layout.addWidget(self.download_audio_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        main_layout.addWidget(self.console)

        # Add Report button
        self.report_button = QPushButton("Report")
        self.report_button.setFixedSize(100, 30)
        self.report_button.clicked.connect(self.report_issue)
        main_layout.addWidget(self.report_button)

        # Add social media links
        social_layout = QHBoxLayout()
        telegram_button = QPushButton("Telegram")
        telegram_button.clicked.connect(self.open_telegram)
        social_layout.addWidget(telegram_button)
        facebook_button = QPushButton("Facebook")
        facebook_button.clicked.connect(self.open_facebook)
        social_layout.addWidget(facebook_button)
        main_layout.addLayout(social_layout)

        # Add copyright text and Instagram link
        copyright_layout = QHBoxLayout()
        copyright_label = QLabel("جميع الحقوق محفوظة © نوح تك | NouhTech")
        copyright_layout.addWidget(copyright_label)
    
        main_layout.addLayout(copyright_layout)

        self.central_widget.setLayout(main_layout)

    def fetch_info(self):
        url = self.url_input.text()
        if url:
            self.video_info_label.clear()
            self.thumbnail_label.clear()
            self.video_info_label.setText("Fetching video info...")
            self.thumbnail_label.setText("")

            self.video_worker = VideoInfoWorker(url)
            self.video_worker.finished.connect(self.display_video_info)
            self.video_worker.start()

    def display_video_info(self, title, thumbnail_data):
        self.video_info_label.setText(title)
        thumbnail_image = QImage()
        thumbnail_image.loadFromData(thumbnail_data)
        thumbnail_image = thumbnail_image.scaled(600, 400, Qt.KeepAspectRatio)
        self.thumbnail_label.setPixmap(QPixmap.fromImage(thumbnail_image))

        self.video_quality_combo.clear()
        self.video_quality_combo.addItem("Choose Video Quality...")
        self.video_quality_combo.setEnabled(True)

        self.audio_quality_combo.clear()
        self.audio_quality_combo.addItem("Choose Audio Quality...")
        self.audio_quality_combo.setEnabled(True)

        yt = YouTube(self.url_input.text())
        for stream in yt.streams.filter(progressive=True):
            self.video_quality_combo.addItem(stream.resolution)

        for stream in yt.streams.filter(only_audio=True):
            self.audio_quality_combo.addItem(stream.abr)

        self.download_video_button.setEnabled(True)
        self.download_audio_button.setEnabled(True)

    def select_save_location(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder_path:
            self.save_path_input.setText(folder_path)

    def download_video(self):
        url = self.url_input.text()
        save_path = self.save_path_input.text()
        quality = self.video_quality_combo.currentText()

        if url and save_path and quality != "Choose Video Quality...":
            self.progress_bar.setValue(0)
            self.console.append("Downloading video...")
            self.download_worker = DownloadWorker(url, save_path, quality)
            self.download_worker.progress.connect(self.update_progress)
            self.download_worker.start()

    def download_audio(self):
        url = self.url_input.text()
        save_path = self.save_path_input.text()
        quality = self.audio_quality_combo.currentText()

        if url and save_path and quality != "Choose Audio Quality...":
            self.progress_bar.setValue(0)
            self.console.append("Downloading audio...")
            self.download_worker = DownloadWorker(url, save_path, quality, audio_only=True)
            self.download_worker.progress.connect(self.update_progress)
            self.download_worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        if value == 100:
            self.console.append("Download complete.")

    def report_issue(self):
        webbrowser.open("https://github.com/chadx0/youtube-download/issues")

    def open_telegram(self):
        webbrowser.open("https://telegram.me/nouhtech")

    def open_facebook(self):
        webbrowser.open("https://x.com/nouh_tech")

class DownloadWorker(QThread):
    progress = pyqtSignal(int)

    def __init__(self, url, save_path, quality, audio_only=False):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.quality = quality
        self.audio_only = audio_only

    def run(self):
        try:
            yt = YouTube(self.url)
            if self.audio_only:
                stream = yt.streams.filter(only_audio=True, abr=self.quality).first()
            else:
                stream = yt.streams.filter(progressive=True, resolution=self.quality).first()

            stream.download(self.save_path)

            # Emit progress signal when download is complete
            self.progress.emit(100)
        except Exception as e:
            print(e)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
