import sys
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.logger import logger
from core.infrastructure.config_manager import config
from core.utils.project_initializer import ProjectInitializer

def main():
    # 1. Initialize Logger
    logger.info("Starting LuminaAI application...")
    
    # 2. Run Project Initialization (Create dirs, migrate files)
    initializer = ProjectInitializer()
    initializer.execute()
    
    # 3. Load Config
    lang = config.get("system.language", "en_US")
    logger.info(f"Loaded configuration. Language: {lang}")

    # 3. Setup Application
    app = QApplication(sys.argv)
    
    # Apply Dark Theme (Simple QSS for now)
    app.setStyleSheet("""
        QMainWindow {
            background-color: #2b2b2b;
        }
        QLabel {
            color: #ffffff;
        }
    """)

    # 4. Launch Main Window
    window = MainWindow()
    window.show()

    logger.info("Main window displayed.")
    
    # 5. Event Loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
