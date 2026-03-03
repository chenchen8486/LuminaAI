import sys
from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LuminaAI - Deep Learning Vision Platform")
        self.resize(1280, 720)
        self._setup_ui()
        self._center_window()

    def _setup_ui(self):
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)

        # Title Label
        title_label = QLabel("LuminaAI")
        title_label.setFont(QFont("Arial", 36, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        
        # Subtitle
        subtitle_label = QLabel("VisionForge Engine Initialized")
        subtitle_label.setFont(QFont("Arial", 18))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #888888;")

        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)

    def _center_window(self):
        screen = self.screen().availableGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
