import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QSpinBox, QFileDialog, QProgressBar, QTextEdit,
    QGroupBox, QSplitter, QListWidget
)
from PySide6.QtCore import Qt, QThread, Signal
from ui.wizards.base_wizard_page import BaseWizardPage
from core.export.model_exporter import ExportWorker
from core.inference.inference_engine import BatchInferenceEngine

class InferenceWorker(QThread):
    """
    Background worker for batch inference.
    """
    log_message = Signal(str)
    progress_update = Signal(int, int) # current, total
    finished = Signal(str) # output_dir
    error = Signal(str)

    def __init__(self, model_path, input_dir, output_dir, device='cpu'):
        super().__init__()
        self.model_path = model_path
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.device = device

    def run(self):
        try:
            self.log_message.emit(f"初始化推理引擎 (Device: {self.device})...")
            engine = BatchInferenceEngine(self.model_path, device=self.device)
            
            self.log_message.emit(f"开始扫描图片: {self.input_dir}")
            results = engine.run_inference(self.input_dir)
            
            total = len(results)
            self.log_message.emit(f"找到 {total} 张图片，开始推理...")
            
            os.makedirs(self.output_dir, exist_ok=True)
            
            for i, result in enumerate(results):
                # Save visualization
                engine.visualize_result(result, save_dir=self.output_dir)
                
                msg = f"[{i+1}/{total}] {os.path.basename(result.image_path)}: {len(result.detections)} detections"
                self.log_message.emit(msg)
                self.progress_update.emit(i + 1, total)
            
            self.log_message.emit(f"推理完成！结果已保存至: {self.output_dir}")
            self.finished.emit(self.output_dir)
            
        except Exception as e:
            import traceback
            self.error.emit(f"推理失败: {str(e)}\n{traceback.format_exc()}")

class Step5Export(BaseWizardPage):
    def __init__(self, controller):
        super().__init__(controller)
        self.export_worker = None
        self.inference_worker = None

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Splitter for Export (Left) and Inference (Right)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # --- Left Panel: Model Export ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        export_group = QGroupBox("模型导出 (Model Export)")
        export_layout = QVBoxLayout()
        
        # Model Path
        model_layout = QHBoxLayout()
        self.model_path_label = QLabel("未选择模型")
        self.model_path_label.setWordWrap(True)
        btn_browse_model = QPushButton("选择模型 (.pt)")
        btn_browse_model.clicked.connect(self._browse_model)
        model_layout.addWidget(self.model_path_label)
        model_layout.addWidget(btn_browse_model)
        export_layout.addLayout(model_layout)
        
        # Format
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("导出格式:"))
        self.combo_format = QComboBox()
        self.combo_format.addItems(["onnx", "torchscript", "engine"]) # engine usually requires tensorrt
        format_layout.addWidget(self.combo_format)
        
        format_layout.addWidget(QLabel("Image Size:"))
        self.spin_imgsz = QSpinBox()
        self.spin_imgsz.setRange(32, 1280)
        self.spin_imgsz.setValue(640)
        self.spin_imgsz.setSingleStep(32)
        format_layout.addWidget(self.spin_imgsz)
        export_layout.addLayout(format_layout)
        
        # Export Button
        self.btn_export = QPushButton("开始导出 (Start Export)")
        self.btn_export.clicked.connect(self._start_export)
        export_layout.addWidget(self.btn_export)
        
        # Progress Bar
        self.export_progress = QProgressBar()
        self.export_progress.setVisible(False)
        export_layout.addWidget(self.export_progress)
        
        # Console
        self.export_console = QTextEdit()
        self.export_console.setReadOnly(True)
        export_layout.addWidget(self.export_console)
        
        export_group.setLayout(export_layout)
        left_layout.addWidget(export_group)
        
        # --- Right Panel: Batch Inference ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        infer_group = QGroupBox("批量推理 (Batch Inference)")
        infer_layout = QVBoxLayout()
        
        # Input Dir
        input_layout = QHBoxLayout()
        self.input_dir_label = QLabel("未选择图片文件夹")
        self.input_dir_label.setWordWrap(True)
        btn_browse_input = QPushButton("选择图片文件夹")
        btn_browse_input.clicked.connect(self._browse_input)
        input_layout.addWidget(self.input_dir_label)
        input_layout.addWidget(btn_browse_input)
        infer_layout.addLayout(input_layout)
        
        # Device
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("推理设备:"))
        self.combo_device = QComboBox()
        self.combo_device.addItems(["cpu", "0", "1"]) # 0/1 for GPU
        device_layout.addWidget(self.combo_device)
        infer_layout.addLayout(device_layout)
        
        # Run Button
        self.btn_infer = QPushButton("运行批量推理 (Run Inference)")
        self.btn_infer.clicked.connect(self._start_inference)
        infer_layout.addWidget(self.btn_infer)
        
        # Progress
        self.infer_progress = QProgressBar()
        self.infer_progress.setVisible(False)
        infer_layout.addWidget(self.infer_progress)
        
        # Console/List
        self.infer_console = QListWidget()
        infer_layout.addWidget(self.infer_console)
        
        infer_group.setLayout(infer_layout)
        right_layout.addWidget(infer_group)
        
        # Add to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

    def _browse_model(self):
        # Default to runs/train if exists
        start_dir = os.path.join(os.getcwd(), "runs", "train")
        if not os.path.exists(start_dir):
            start_dir = os.getcwd()
            
        path, _ = QFileDialog.getOpenFileName(self, "选择模型权重", start_dir, "PyTorch Model (*.pt)")
        if path:
            self.model_path_label.setText(path)
            self.export_console.append(f"已选择模型: {path}")

    def _browse_input(self):
        path = QFileDialog.getExistingDirectory(self, "选择图片文件夹", os.getcwd())
        if path:
            self.input_dir_label.setText(path)
            self.infer_console.addItem(f"已选择输入文件夹: {path}")

    def _start_export(self):
        model_path = self.model_path_label.text()
        if not os.path.exists(model_path):
            self.export_console.append("错误: 请先选择有效的模型文件！")
            return
            
        fmt = self.combo_format.currentText()
        imgsz = self.spin_imgsz.value()
        
        self.btn_export.setEnabled(False)
        self.export_progress.setVisible(True)
        self.export_progress.setRange(0, 0) # Indeterminate
        self.export_console.append(">>> 开始导出任务...")
        
        self.export_worker = ExportWorker(model_path, fmt, imgsz)
        self.export_worker.progress_update.connect(lambda msg: self.export_console.append(msg))
        self.export_worker.export_finished.connect(self._on_export_finished)
        self.export_worker.error_occurred.connect(self._on_export_error)
        self.export_worker.start()

    def _on_export_finished(self, path):
        self.btn_export.setEnabled(True)
        self.export_progress.setRange(0, 100)
        self.export_progress.setValue(100)
        self.export_console.append(f"✅ 导出成功: {path}")
        # Optionally open folder
        # os.startfile(os.path.dirname(path))

    def _on_export_error(self, msg):
        self.btn_export.setEnabled(True)
        self.export_progress.setVisible(False)
        self.export_console.append(f"❌ 导出失败: {msg}")

    def _start_inference(self):
        model_path = self.model_path_label.text()
        input_dir = self.input_dir_label.text()
        
        if not os.path.exists(model_path):
            self.infer_console.addItem("错误: 请先在左侧选择模型文件！")
            return
        if not os.path.exists(input_dir):
            self.infer_console.addItem("错误: 请选择有效的输入图片文件夹！")
            return
            
        output_dir = os.path.join(input_dir, "inference_results")
        device = self.combo_device.currentText()
        
        self.btn_infer.setEnabled(False)
        self.infer_progress.setVisible(True)
        self.infer_progress.setValue(0)
        self.infer_console.addItem(">>> 开始批量推理...")
        
        self.inference_worker = InferenceWorker(model_path, input_dir, output_dir, device)
        self.inference_worker.log_message.connect(lambda msg: self.infer_console.addItem(msg))
        self.inference_worker.progress_update.connect(self._update_infer_progress)
        self.inference_worker.finished.connect(self._on_infer_finished)
        self.inference_worker.error.connect(self._on_infer_error)
        self.inference_worker.start()

    def _update_infer_progress(self, current, total):
        self.infer_progress.setRange(0, total)
        self.infer_progress.setValue(current)

    def _on_infer_finished(self, output_dir):
        self.btn_infer.setEnabled(True)
        self.infer_console.addItem(f"✅ 推理完成！结果保存在: {output_dir}")
        self.infer_console.scrollToBottom()

    def _on_infer_error(self, msg):
        self.btn_infer.setEnabled(True)
        self.infer_console.addItem(f"❌ 推理出错: {msg}")

    def validate_page(self) -> bool:
        return True # Step 5 is optional/final, no strict validation to proceed
