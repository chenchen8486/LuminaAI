from PySide6.QtWidgets import QWidget, QVBoxLayout

class BaseWizardPage(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._setup_ui()

    def _setup_ui(self):
        """Override this method to setup page UI"""
        self.layout = QVBoxLayout(self)

    def on_enter(self):
        """Called when this page is shown"""
        pass

    def on_leave(self):
        """Called before leaving this page. Return False to prevent navigation."""
        return True
