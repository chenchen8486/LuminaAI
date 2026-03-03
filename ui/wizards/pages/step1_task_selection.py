from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PySide6.QtCore import Qt
from ui.wizards.base_wizard_page import BaseWizardPage

class Step1TaskSelection(BaseWizardPage):
    def __init__(self, controller):
        super().__init__(controller)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Title
        title = QLabel("Step 1: 选择任务类型")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        # Cards Layout
        cards_layout = QHBoxLayout()
        
        self.btn_detect = self._create_card("目标检测", "识别物体位置与类别")
        self.btn_segment = self._create_card("图像分割", "像素级抠图")
        self.btn_classify = self._create_card("图像分类", "整图识别")

        cards_layout.addWidget(self.btn_detect)
        cards_layout.addWidget(self.btn_segment)
        cards_layout.addWidget(self.btn_classify)
        
        layout.addLayout(cards_layout)
        
        # Connect signals
        self.btn_detect.clicked.connect(lambda: self._select_task("detection"))
        self.btn_segment.clicked.connect(lambda: self._select_task("segmentation"))
        self.btn_classify.clicked.connect(lambda: self._select_task("classification"))

    def _create_card(self, title, desc):
        btn = QPushButton(f"{title}\n\n{desc}")
        btn.setFixedSize(200, 250)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                border: 2px solid #555;
                border-radius: 10px;
                font-size: 18px;
                color: white;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #007acc;
            }
            QPushButton:checked {
                background-color: #007acc;
                border-color: #009ce0;
            }
        """)
        btn.setCheckable(True)
        return btn

    def _select_task(self, task_type):
        # Update UI state
        self.btn_detect.setChecked(task_type == "detection")
        self.btn_segment.setChecked(task_type == "segmentation")
        self.btn_classify.setChecked(task_type == "classification")
        
        # Update Controller
        self.controller.set_data("task_type", task_type)
        print(f"Task selected: {task_type}")
