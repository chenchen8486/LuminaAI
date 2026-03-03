import sys
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from ui.wizards.wizard_container import WizardContainer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LuminaAI - Deep Learning Vision Platform")
        self.resize(1280, 720)
        self._setup_ui()
        self._center_window()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Wizard Container
        self.wizard = WizardContainer()
        layout.addWidget(self.wizard)

    def _center_window(self):
        screen = self.screen().availableGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
