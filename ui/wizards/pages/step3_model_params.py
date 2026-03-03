from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QFormLayout, QSpinBox, QPushButton, QGroupBox, QDoubleSpinBox
from PySide6.QtCore import Qt
from ui.wizards.base_wizard_page import BaseWizardPage

class Step3ModelParams(BaseWizardPage):
    def __init__(self, controller):
        super().__init__(controller)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("Step 3: 模型与参数配置")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        # Main Container
        container = QWidget()
        container.setFixedWidth(500)
        container_layout = QVBoxLayout(container)
        
        # --- Basic Settings ---
        basic_group = QGroupBox("基础设置 (Basic)")
        basic_form = QFormLayout(basic_group)
        
        # Model Selection
        self.combo_model = QComboBox()
        self.combo_model.addItems(["YOLOv8-Nano", "YOLOv8-Small", "YOLOv8-Medium", "ResNet-50"])
        self.combo_model.currentTextChanged.connect(lambda t: self.controller.set_data("model_name", t))
        basic_form.addRow("基础模型:", self.combo_model)

        # Epochs
        self.spin_epochs = QSpinBox()
        self.spin_epochs.setRange(1, 10000)
        self.spin_epochs.setValue(100)
        self.spin_epochs.valueChanged.connect(lambda v: self.controller.set_data("epochs", v))
        basic_form.addRow("训练轮数 (Epochs):", self.spin_epochs)
        
        # Batch Size
        self.spin_batch = QSpinBox()
        self.spin_batch.setRange(1, 128)
        self.spin_batch.setValue(16)
        self.spin_batch.valueChanged.connect(lambda v: self.controller.set_data("batch_size", v))
        basic_form.addRow("批次大小 (Batch Size):", self.spin_batch)
        
        container_layout.addWidget(basic_group)

        # --- Advanced Settings Toggle ---
        self.btn_toggle_advanced = QPushButton("▼ 展开高级设置 (Advanced)")
        self.btn_toggle_advanced.setCheckable(True)
        self.btn_toggle_advanced.setStyleSheet("""
            QPushButton { border: none; color: #888; text-align: left; padding: 5px; }
            QPushButton:hover { color: #aaa; }
            QPushButton:checked { color: #007acc; }
        """)
        self.btn_toggle_advanced.clicked.connect(self._toggle_advanced)
        container_layout.addWidget(self.btn_toggle_advanced)

        # --- Advanced Settings Content ---
        self.advanced_group = QGroupBox("高级参数 (Hyperparameters)")
        self.advanced_group.setVisible(False)
        adv_form = QFormLayout(self.advanced_group)

        # Learning Rate (lr0)
        self.spin_lr0 = QDoubleSpinBox()
        self.spin_lr0.setRange(0.0001, 0.1)
        self.spin_lr0.setSingleStep(0.001)
        self.spin_lr0.setDecimals(4)
        self.spin_lr0.setValue(0.01)
        self.spin_lr0.valueChanged.connect(lambda v: self.controller.set_data("lr0", v))
        adv_form.addRow("初始学习率 (lr0):", self.spin_lr0)

        # Image Size
        self.spin_imgsz = QSpinBox()
        self.spin_imgsz.setRange(320, 1280)
        self.spin_imgsz.setSingleStep(32)
        self.spin_imgsz.setValue(640)
        self.spin_imgsz.valueChanged.connect(lambda v: self.controller.set_data("imgsz", v))
        adv_form.addRow("输入尺寸 (ImgSz):", self.spin_imgsz)

        # Workers
        self.spin_workers = QSpinBox()
        self.spin_workers.setRange(0, 16)
        self.spin_workers.setValue(4)
        self.spin_workers.valueChanged.connect(lambda v: self.controller.set_data("workers", v))
        adv_form.addRow("数据加载线程 (Workers):", self.spin_workers)

        container_layout.addWidget(self.advanced_group)
        
        layout.addWidget(container, alignment=Qt.AlignCenter)
        
        # Initialize default values
        self._init_defaults()

    def _toggle_advanced(self, checked):
        self.advanced_group.setVisible(checked)
        self.btn_toggle_advanced.setText("▲ 收起高级设置 (Advanced)" if checked else "▼ 展开高级设置 (Advanced)")

    def _init_defaults(self):
        self.controller.set_data("model_name", self.combo_model.currentText())
        self.controller.set_data("epochs", self.spin_epochs.value())
        self.controller.set_data("batch_size", self.spin_batch.value())
        self.controller.set_data("lr0", self.spin_lr0.value())
        self.controller.set_data("imgsz", self.spin_imgsz.value())
        self.controller.set_data("workers", self.spin_workers.value())
