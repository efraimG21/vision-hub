import os
from PySide6.QtCore import Qt, QUrl, QSize, QTime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton,
    QLabel, QListWidgetItem, QSlider, QFrame
)
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget


class MediaPlayerWidget(QWidget):
    def __init__(self, recordings_dir):
        super().__init__()
        self.recordings_dir = recordings_dir

        self.player = QMediaPlayer()
        self.player.durationChanged.connect(self.update_duration)
        self.player.positionChanged.connect(self.update_position)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(25)
        self.setLayout(main_layout)

        left_panel = QVBoxLayout()
        left_panel.setSpacing(15)

        self.refresh_btn = QPushButton("🔄 Refresh Recordings")
        self.refresh_btn.setFixedHeight(65)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                font-size: 20px;
                font-weight: bold;
                border-radius: 15px;
                padding: 10px;
            }
            QPushButton:pressed {
                background-color: #005fa3;
            }
        """)

        self.list_widget = QListWidget()
        self.list_widget.setFrameShape(QFrame.NoFrame)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #2a2a2a;
                color: white;
                font-size: 16px;
                border-radius: 15px;
                padding: 10px;
            }
            QListWidget::item {
                padding: 18px;
                margin-bottom: 6px;
                border-radius: 10px;
            }
            QListWidget::item:selected {
                background-color: #444;
            }
        """)

        left_panel.addWidget(self.refresh_btn)
        left_panel.addWidget(self.list_widget)

        right_panel = QVBoxLayout()
        right_panel.setSpacing(20)

        self.video_title = QLabel("📼 Select a recording")
        self.video_title.setAlignment(Qt.AlignCenter)
        self.video_title.setStyleSheet("""
            color: white;
            font-size: 30px;
            font-weight: bold;
            padding: 5px;
        """)

        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("""
            background-color: black;
            border-radius: 20px;
        """)

        seek_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")

        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.setStyleSheet("""
            QSlider {
                height: 40px;
            }
            QSlider::groove:horizontal {
                height: 12px;
                background: #555;
                border-radius: 6px;
            }
            QSlider::handle:horizontal {
                background: #0078d4;
                width: 32px;
                height: 32px;
                margin: -12px 0;
                border-radius: 16px;
            }
        """)
        self.seek_slider.sliderMoved.connect(self.seek_video)

        self.total_time_label = QLabel("00:00")
        self.total_time_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")

        seek_layout.addWidget(self.current_time_label)
        seek_layout.addWidget(self.seek_slider, 1)
        seek_layout.addWidget(self.total_time_label)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(30)

        self.rewind_btn = QPushButton("⏪ 10s")
        self.play_pause_btn = QPushButton("▶️ Play")
        self.stop_btn = QPushButton("⏹ Stop")
        self.forward_btn = QPushButton("10s ⏩")

        buttons = [self.rewind_btn, self.play_pause_btn, self.stop_btn, self.forward_btn]
        for btn in buttons:
            btn.setFixedSize(150, 70)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #444;
                    color: white;
                    font-size: 24px;
                    font-weight: bold;
                    border-radius: 15px;
                }
                QPushButton:pressed {
                    background-color: #666;
                }
            """)
            controls_layout.addWidget(btn)

        # 🏗 Assemble right layout
        right_panel.addWidget(self.video_title)
        right_panel.addWidget(self.video_widget, 1)
        right_panel.addLayout(seek_layout)
        right_panel.addLayout(controls_layout)

        # Add to main layout
        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 2)

        self.player.setVideoOutput(self.video_widget)

        self.refresh_btn.clicked.connect(self.load_video_list)
        self.list_widget.itemDoubleClicked.connect(self.play_selected_video)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        self.stop_btn.clicked.connect(self.stop_video)
        self.rewind_btn.clicked.connect(lambda: self.skip_seconds(-10))
        self.forward_btn.clicked.connect(lambda: self.skip_seconds(10))

        self.load_video_list()

        self.is_playing = False
        self.current_video_path = None

    def load_video_list(self):
        """Load MP4 recordings into the list."""
        self.list_widget.clear()
        if not os.path.exists(self.recordings_dir):
            os.makedirs(self.recordings_dir)

        videos = [f for f in os.listdir(self.recordings_dir) if f.endswith(".mp4")]
        videos.sort(reverse=True)

        if not videos:
            self.video_title.setText("⚠️ No recordings found.")
            return

        for video in videos:
            item = QListWidgetItem(f"📹 {video}")
            item.setSizeHint(item.sizeHint() + QSize(0, 25))  # More padding for tablet
            self.list_widget.addItem(item)

    def play_selected_video(self):
        """Play the selected video when double-clicked."""
        selected = self.list_widget.currentItem()
        if not selected:
            return

        self.current_video_path = os.path.join(self.recordings_dir, selected.text()[2:])
        self.player.setSource(QUrl.fromLocalFile(self.current_video_path))
        self.player.play()

        self.video_title.setText(f"▶️ Playing: {selected.text()[2:]}")
        self.play_pause_btn.setText("⏸ Pause")
        self.is_playing = True

    def toggle_play_pause(self):
        if self.is_playing:
            self.player.pause()
            self.play_pause_btn.setText("▶️ Play")
        else:
            self.player.play()
            self.play_pause_btn.setText("⏸ Pause")
        self.is_playing = not self.is_playing

    def stop_video(self):
        self.player.stop()
        self.play_pause_btn.setText("▶️ Play")
        self.is_playing = False

    def update_duration(self, duration):
        self.seek_slider.setRange(0, duration)
        self.total_time_label.setText(self.format_time(duration))

    def update_position(self, position):
        self.seek_slider.blockSignals(True)
        self.seek_slider.setValue(position)
        self.seek_slider.blockSignals(False)
        self.current_time_label.setText(self.format_time(position))

    def seek_video(self, position):
        self.player.setPosition(position)

    def format_time(self, ms):
        """Convert milliseconds to mm:ss."""
        secs = ms // 1000
        return QTime(0, secs // 60, secs % 60).toString("mm:ss")

    def skip_seconds(self, seconds):
        """Jump forward or backward by X seconds."""
        new_pos = self.player.position() + (seconds * 1000)
        self.player.setPosition(max(0, new_pos))
