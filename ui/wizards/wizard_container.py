from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QMessageBox
from ui.wizards.wizard_controller import wizard_controller
from ui.wizards.pages.step1_task_selection import Step1TaskSelection
from ui.wizards.pages.step2_data_import import Step2DataImport
from ui.wizards.pages.step3_model_params import Step3ModelParams

class WizardContainer(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = wizard_controller
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Stacked Widget for pages
        self.stacked_widget = QStackedWidget()
        self.step1 = Step1TaskSelection(self.controller)
        self.step2 = Step2DataImport(self.controller)
        self.step3 = Step3ModelParams(self.controller)
        
        self.stacked_widget.addWidget(self.step1)
        self.stacked_widget.addWidget(self.step2)
        self.stacked_widget.addWidget(self.step3)
        
        main_layout.addWidget(self.stacked_widget)
        
        # Navigation Bar
        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("上一步")
        self.btn_next = QPushButton("下一步")
        
        self.btn_prev.clicked.connect(self.controller.prev_step)
        self.btn_next.clicked.connect(self._on_next_clicked)
        
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_next)
        
        main_layout.addLayout(nav_layout)
        
        self._update_nav_buttons(0)

    def _connect_signals(self):
        self.controller.page_changed.connect(self._on_page_changed)

    def _on_page_changed(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self._update_nav_buttons(index)

    def _on_next_clicked(self):
        is_valid, error_msg = self.controller.validate_current_step()
        if is_valid:
            self.controller.next_step()
        else:
            QMessageBox.warning(self, "提示", error_msg)

    def _update_nav_buttons(self, index):
        self.btn_prev.setEnabled(index > 0)
        self.btn_next.setText("完成" if index == 2 else "下一步")
