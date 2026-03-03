from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from ui.wizards.base_wizard_page import BaseWizardPage

class Step5Export(BaseWizardPage):
    def __init__(self, controller):
        super().__init__(controller)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("Step 5: 模型导出 (Coming Soon)")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        desc = QLabel("此功能将在 Phase 4 中实现。\n包含: ONNX 导出, 批量推理, 评估报告")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
