import sys
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtCore import Qt
from ui.wizards.wizard_container import WizardContainer
from ui.wizards.wizard_controller import wizard_controller
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LuminaAI - Deep Learning Vision Platform")
        self.resize(1280, 720)
        
        self.current_bg_pixmap = None
        self._load_background(0)
        
        self._setup_ui()
        self._center_window()
        
        # Connect to wizard controller to change background
        wizard_controller.page_changed.connect(self._on_page_changed)

    def _setup_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        # Make central widget transparent so background shows through
        central_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20) # Add some margin
        
        # Wizard Container
        self.wizard = WizardContainer()
        # Ensure wizard container is also transparent or semi-transparent
        self.wizard.setAttribute(Qt.WA_TranslucentBackground)
        layout.addWidget(self.wizard)

    def _load_background(self, page_index):
        """Loads the background image based on the page index."""
        # Map page index to image file
        # 0: Task Selection -> 1.jpg
        # 1: Data Import -> 2.jpg
        # 2: Model Params -> 2.jpg (Reuse)
        # 3: Training -> 3.jpg
        # 4: Export -> 4.jpg
        
        image_map = {
            0: "1.jpg",
            1: "2.jpg",
            2: "2.jpg", 
            3: "3.jpg",
            4: "4.jpg"
        }
        
        filename = image_map.get(page_index, "1.jpg")
        bg_path = os.path.join(os.path.dirname(__file__), "picture", filename)
        
        if os.path.exists(bg_path):
            self.current_bg_pixmap = QPixmap(bg_path)
        else:
            print(f"Warning: Background image not found: {bg_path}")
            self.current_bg_pixmap = None
        
        self.update() # Trigger repaint

    def _on_page_changed(self, index):
        self._load_background(index)

    def paintEvent(self, event):
        """Draws the background image scaled to fill the window."""
        painter = QPainter(self)
        if self.current_bg_pixmap:
            # Scale the pixmap to cover the entire window (AspectFill equivalent)
            scaled_pixmap = self.current_bg_pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            
            # Calculate position to center the image
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            
            painter.drawPixmap(x, y, scaled_pixmap)
        else:
            # Fallback color if no image
            painter.fillRect(self.rect(), Qt.darkGray)
            
        super().paintEvent(event)

    def _center_window(self):
        screen = self.screen().availableGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
