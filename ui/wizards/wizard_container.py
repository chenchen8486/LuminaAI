from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QMessageBox, QFrame, QLabel
from ui.wizards.wizard_controller import wizard_controller
from ui.wizards.pages.step1_task_selection import Step1TaskSelection
from ui.wizards.pages.step2_data_import import Step2DataImport
from ui.wizards.pages.step3_model_params import Step3ModelParams
from ui.wizards.pages.step4_training import Step4Training
from ui.wizards.pages.step5_export import Step5Export
from ui.styles import UIStyles

class WizardContainer(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = wizard_controller
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked Widget for pages
        self.stacked_widget = QStackedWidget()
        # Remove the global foggy background
        self.stacked_widget.setStyleSheet("background-color: transparent;")
        
        self.step1 = Step1TaskSelection(self.controller)
        self.step2 = Step2DataImport(self.controller)
        self.step3 = Step3ModelParams(self.controller)
        self.step4 = Step4Training(self.controller)
        self.step5 = Step5Export(self.controller)
        
        self.stacked_widget.addWidget(self.step1)
        self.stacked_widget.addWidget(self.step2)
        self.stacked_widget.addWidget(self.step3)
        self.stacked_widget.addWidget(self.step4)
        self.stacked_widget.addWidget(self.step5)
        
        main_layout.addWidget(self.stacked_widget)
        
        # Navigation Bar (Bottom)
        nav_container = QFrame()
        nav_container.setStyleSheet("background-color: transparent;")
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(40, 20, 40, 20)
        
        self.btn_prev = QPushButton("上一步")
        self.btn_next = QPushButton("下一步")
        
        # Apply styles
        self.btn_prev.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(30, 30, 30, 0.8);
                color: {UIStyles.TEXT_GRAY};
                border: 1px solid #444;
                border-radius: 6px;
                font-size: 16px;
                padding: 12px 30px;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: #444;
                color: {UIStyles.TEXT_WHITE};
            }}
            QPushButton:disabled {{
                background-color: transparent;
                color: #555;
                border-color: #333;
            }}
        """)
        
        self.btn_next.setStyleSheet(f"""
            QPushButton {{
                background-color: {UIStyles.ACCENT_GREEN};
                color: {UIStyles.TEXT_BLACK};
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
                padding: 12px 40px;
                min-width: 140px;
            }}
            QPushButton:hover {{
                background-color: {UIStyles.ACCENT_HOVER};
            }}
        """)
        
        self.btn_prev.clicked.connect(self.controller.prev_step)
        self.btn_next.clicked.connect(self._on_next_clicked)
        
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_next)
        
        main_layout.addWidget(nav_container)
        
        self._update_nav_buttons(0)

    def _connect_signals(self):
        self.controller.page_changed.connect(self._on_page_changed)

    def _on_page_changed(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self._update_nav_buttons(index)

    def _on_next_clicked(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index == 4: # Last Step
            QMessageBox.information(self, "完成", "所有步骤已完成！您可以开始新的任务。")
            self.controller.reset()
            return

        is_valid, error_msg = self.controller.validate_current_step()
        if is_valid:
            self.controller.next_step()
        else:
            QMessageBox.warning(self, "提示", error_msg)

    def _update_nav_buttons(self, index):
        self.btn_prev.setEnabled(index > 0)
        
        if index == 4: # Last step (Export)
            self.btn_next.setText("完成")
        elif index == 3: # Training step
            # Can only proceed if training is done, logic handled in controller validation
            self.btn_next.setText("下一步")
        else:
            self.btn_next.setText("下一步")
