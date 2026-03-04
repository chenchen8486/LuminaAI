import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QSpinBox, QFileDialog, QProgressBar, QTextEdit,
    QGroupBox, QSplitter, QListWidget, QCheckBox, QDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal
from ui.wizards.base_wizard_page import BaseWizardPage
from core.export.model_exporter import ExportWorker
from core.inference.inference_engine import BatchInferenceEngine
from core.inference.evaluator import Evaluator, EvaluationReport
from ui.styles import UIStyles

class EvaluationDialog(QDialog):
    def __init__(self, report: EvaluationReport, parent=None):
        super().__init__(parent)
        self.setWindowTitle("评估报告 (Evaluation Report)")
        self.resize(800, 600)
        self._setup_ui(report)

    def _setup_ui(self, report):
        layout = QVBoxLayout(self)
        
        # 1. Overall Metrics
        overall_group = QGroupBox("总体指标 (Overall Metrics)")
        overall_layout = QHBoxLayout()
        
        metrics = [
            ("mAP/F1", f"{report.overall_metrics.f1:.4f}"),
            ("Precision", f"{report.overall_metrics.precision:.4f}"),
            ("Recall", f"{report.overall_metrics.recall:.4f}"),
            ("True Positives", str(report.overall_metrics.tp)),
            ("False Positives", str(report.overall_metrics.fp)),
            ("False Negatives", str(report.overall_metrics.fn))
        ]
        
        for name, value in metrics:
            lbl = QLabel(f"{name}: <b>{value}</b>")
            lbl.setTextFormat(Qt.RichText)
            overall_layout.addWidget(lbl)
            
        overall_group.setLayout(overall_layout)
        layout.addWidget(overall_group)
        
        # 2. Class Metrics Table
        table_group = QGroupBox("类别详情 (Class Metrics)")
        table_layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Class Name", "Precision", "Recall", "F1", "FP", "FN"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.table.setRowCount(len(report.class_metrics))
        
        for row, (cls_id, cls_metric) in enumerate(report.class_metrics.items()):
            self.table.setItem(row, 0, QTableWidgetItem(str(cls_id)))
            self.table.setItem(row, 1, QTableWidgetItem(cls_metric.class_name))
            self.table.setItem(row, 2, QTableWidgetItem(f"{cls_metric.metrics.precision:.4f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{cls_metric.metrics.recall:.4f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{cls_metric.metrics.f1:.4f}"))
            self.table.setItem(row, 5, QTableWidgetItem(str(cls_metric.metrics.fp)))
            self.table.setItem(row, 6, QTableWidgetItem(str(cls_metric.metrics.fn)))
            
        table_layout.addWidget(self.table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)
        
        # 3. FP/FN Lists
        lists_layout = QHBoxLayout()
        
        fp_group = QGroupBox(f"误报图片 ({len(report.fp_images)})")
        fp_layout = QVBoxLayout()
        fp_list = QListWidget()
        fp_list.addItems([os.path.basename(p) for p in report.fp_images])
        fp_layout.addWidget(fp_list)
        fp_group.setLayout(fp_layout)
        
        fn_group = QGroupBox(f"漏报图片 ({len(report.fn_images)})")
        fn_layout = QVBoxLayout()
        fn_list = QListWidget()
        fn_list.addItems([os.path.basename(p) for p in report.fn_images])
        fn_layout.addWidget(fn_list)
        fn_group.setLayout(fn_layout)
        
        lists_layout.addWidget(fp_group)
        lists_layout.addWidget(fn_group)
        layout.addLayout(lists_layout)


class InferenceWorker(QThread):
    """
    Background worker for batch inference and optional evaluation.
    """
    log_message = Signal(str)
    progress_update = Signal(int, int) # current, total
    finished = Signal(str) # output_dir
    evaluation_finished = Signal(object) # EvaluationReport
    error = Signal(str)

    def __init__(self, model_path, input_dir, output_dir, device='cpu', gt_dir=None):
        super().__init__()
        self.model_path = model_path
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.device = device
        self.gt_dir = gt_dir

    def run(self):
        try:
            self.log_message.emit(f"初始化推理引擎 (Device: {self.device})...")
            engine = BatchInferenceEngine(self.model_path, device=self.device)
            
            # Get class names for evaluation
            class_names = engine.get_class_names()
            
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
            
            # Run Evaluation if GT provided
            if self.gt_dir and os.path.exists(self.gt_dir):
                self.log_message.emit(">>> 正在进行评估 (Calculating Metrics)...")
                evaluator = Evaluator()
                report = evaluator.evaluate(results, self.gt_dir, class_names)
                self.evaluation_finished.emit(report)
                self.log_message.emit("评估完成！请查看报告弹窗。")
            
        except Exception as e:
            import traceback
            self.error.emit(f"推理/评估失败: {str(e)}\n{traceback.format_exc()}")

class Step5Export(BaseWizardPage):
    def __init__(self, controller):
        super().__init__(controller)
        self.export_worker = None
        self.inference_worker = None

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # --- Card Frame ---
        self.card_frame = QFrame()
        self.card_frame.setObjectName("CardContainer")
        self.card_frame.setStyleSheet(UIStyles.CARD_CONTAINER)
        
        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(20, 20, 20, 20)
        
        # Splitter for Export (Left) and Inference (Right)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #444;
                width: 2px;
            }
        """)
        card_layout.addWidget(splitter)
        
        # --- Left Panel: Model Export ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 10, 0)
        
        export_group = QGroupBox("模型导出 (Model Export)")
        export_group.setStyleSheet(UIStyles.GROUP_BOX)
        export_layout = QVBoxLayout()
        
        # Model Path
        model_layout = QHBoxLayout()
        self.model_path_label = QLabel("未选择模型")
        self.model_path_label.setWordWrap(True)
        self.model_path_label.setStyleSheet(UIStyles.LBL_SUBTITLE)
        
        btn_browse_model = QPushButton("选择模型 (.pt)")
        btn_browse_model.setCursor(Qt.PointingHandCursor)
        btn_browse_model.setStyleSheet(UIStyles.BTN_SECONDARY)
        btn_browse_model.clicked.connect(self._browse_model)
        
        model_layout.addWidget(self.model_path_label)
        model_layout.addWidget(btn_browse_model)
        export_layout.addLayout(model_layout)
        
        # Format
        format_layout = QHBoxLayout()
        lbl_fmt = QLabel("导出格式:")
        lbl_fmt.setStyleSheet(f"color: {UIStyles.TEXT_GRAY}")
        format_layout.addWidget(lbl_fmt)
        
        self.combo_format = QComboBox()
        self.combo_format.addItems(["onnx", "torchscript", "engine"]) # engine usually requires tensorrt
        self.combo_format.setStyleSheet("padding: 5px;")
        format_layout.addWidget(self.combo_format)
        
        lbl_sz = QLabel("Image Size:")
        lbl_sz.setStyleSheet(f"color: {UIStyles.TEXT_GRAY}")
        format_layout.addWidget(lbl_sz)
        
        self.spin_imgsz = QSpinBox()
        self.spin_imgsz.setRange(32, 1280)
        self.spin_imgsz.setValue(640)
        self.spin_imgsz.setSingleStep(32)
        self.spin_imgsz.setStyleSheet("padding: 5px;")
        format_layout.addWidget(self.spin_imgsz)
        export_layout.addLayout(format_layout)
        
        # Export Button
        self.btn_export = QPushButton("开始导出 (Start Export)")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setStyleSheet(f"""
            QPushButton {{
                background-color: {UIStyles.ACCENT_GREEN};
                color: {UIStyles.TEXT_BLACK};
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 12px;
                font-size: 16px;
            }}
            QPushButton:hover {{ background-color: {UIStyles.ACCENT_HOVER}; }}
            QPushButton:disabled {{ background-color: #444; color: #666; }}
        """)
        self.btn_export.clicked.connect(self._start_export)
        export_layout.addWidget(self.btn_export)
        
        # Progress Bar
        self.export_progress = QProgressBar()
        self.export_progress.setVisible(False)
        self.export_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #444;
                border-radius: 5px;
                text-align: center;
                color: white;
                background-color: #222;
            }}
            QProgressBar::chunk {{
                background-color: {UIStyles.ACCENT_GREEN};
                width: 20px;
            }}
        """)
        export_layout.addWidget(self.export_progress)
        
        # Console
        self.export_console = QTextEdit()
        self.export_console.setReadOnly(True)
        self.export_console.setStyleSheet(f"background-color: #111; color: {UIStyles.TEXT_GRAY}; font-family: Consolas; border: 1px solid #333;")
        export_layout.addWidget(self.export_console)
        
        export_group.setLayout(export_layout)
        left_layout.addWidget(export_group)
        
        # --- Right Panel: Batch Inference ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        infer_group = QGroupBox("批量推理与评估 (Inference & Eval)")
        infer_group.setStyleSheet(UIStyles.GROUP_BOX)
        infer_layout = QVBoxLayout()
        
        # Input Dir
        input_layout = QHBoxLayout()
        self.input_dir_label = QLabel("未选择图片文件夹")
        self.input_dir_label.setWordWrap(True)
        self.input_dir_label.setStyleSheet(UIStyles.LBL_SUBTITLE)
        
        btn_browse_input = QPushButton("选择图片")
        btn_browse_input.setCursor(Qt.PointingHandCursor)
        btn_browse_input.setStyleSheet(UIStyles.BTN_SECONDARY)
        btn_browse_input.clicked.connect(self._browse_input)
        
        input_layout.addWidget(self.input_dir_label)
        input_layout.addWidget(btn_browse_input)
        infer_layout.addLayout(input_layout)
        
        # GT Dir (Optional)
        gt_layout = QHBoxLayout()
        self.chk_eval = QCheckBox("启用评估 (需提供标注)")
        self.chk_eval.setStyleSheet(f"color: {UIStyles.TEXT_WHITE}")
        self.chk_eval.stateChanged.connect(self._toggle_gt_input)
        
        self.gt_dir_label = QLabel("未选择标注文件夹")
        self.gt_dir_label.setWordWrap(True)
        self.gt_dir_label.setStyleSheet(UIStyles.LBL_SUBTITLE)
        
        self.btn_browse_gt = QPushButton("选择标注")
        self.btn_browse_gt.setCursor(Qt.PointingHandCursor)
        self.btn_browse_gt.setStyleSheet(UIStyles.BTN_SECONDARY)
        self.btn_browse_gt.clicked.connect(self._browse_gt)
        self.btn_browse_gt.setEnabled(False)
        
        gt_layout.addWidget(self.chk_eval)
        gt_layout.addWidget(self.gt_dir_label)
        gt_layout.addWidget(self.btn_browse_gt)
        infer_layout.addLayout(gt_layout)
        
        # Device
        device_layout = QHBoxLayout()
        lbl_dev = QLabel("推理设备:")
        lbl_dev.setStyleSheet(f"color: {UIStyles.TEXT_GRAY}")
        device_layout.addWidget(lbl_dev)
        
        self.combo_device = QComboBox()
        self.combo_device.addItems(["cpu", "0", "1"]) # 0/1 for GPU
        self.combo_device.setStyleSheet("padding: 5px;")
        device_layout.addWidget(self.combo_device)
        infer_layout.addLayout(device_layout)
        
        # Run Button
        self.btn_infer = QPushButton("运行推理 (Run Inference)")
        self.btn_infer.setCursor(Qt.PointingHandCursor)
        self.btn_infer.setStyleSheet(f"""
            QPushButton {{
                background-color: {UIStyles.ACCENT_GREEN};
                color: {UIStyles.TEXT_BLACK};
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 12px;
                font-size: 16px;
            }}
            QPushButton:hover {{ background-color: {UIStyles.ACCENT_HOVER}; }}
            QPushButton:disabled {{ background-color: #444; color: #666; }}
        """)
        self.btn_infer.clicked.connect(self._start_inference)
        infer_layout.addWidget(self.btn_infer)
        
        # Progress
        self.infer_progress = QProgressBar()
        self.infer_progress.setVisible(False)
        self.infer_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #444;
                border-radius: 5px;
                text-align: center;
                color: white;
                background-color: #222;
            }}
            QProgressBar::chunk {{
                background-color: {UIStyles.ACCENT_GREEN};
                width: 20px;
            }}
        """)
        infer_layout.addWidget(self.infer_progress)
        
        # Console/List
        self.infer_console = QListWidget()
        self.infer_console.setStyleSheet(f"background-color: #111; color: {UIStyles.TEXT_GRAY}; border: 1px solid #333;")
        infer_layout.addWidget(self.infer_console)
        
        infer_group.setLayout(infer_layout)
        right_layout.addWidget(infer_group)
        
        # Add to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(self.card_frame)

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

    def _toggle_gt_input(self, state):
        self.btn_browse_gt.setEnabled(state == Qt.Checked)
        if state != Qt.Checked:
            self.gt_dir_label.setText("未选择标注文件夹")

    def _browse_gt(self):
        path = QFileDialog.getExistingDirectory(self, "选择标注文件夹 (YOLO .txt)", os.getcwd())
        if path:
            self.gt_dir_label.setText(path)
            self.infer_console.addItem(f"已选择标注文件夹: {path}")

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
        
        gt_dir = None
        if self.chk_eval.isChecked():
            gt_path = self.gt_dir_label.text()
            if os.path.exists(gt_path):
                gt_dir = gt_path
            else:
                self.infer_console.addItem("警告: 未选择有效的标注文件夹，将跳过评估。")
        
        self.btn_infer.setEnabled(False)
        self.infer_progress.setVisible(True)
        self.infer_progress.setValue(0)
        self.infer_console.addItem(">>> 开始批量推理...")
        
        self.inference_worker = InferenceWorker(model_path, input_dir, output_dir, device, gt_dir)
        self.inference_worker.log_message.connect(lambda msg: self.infer_console.addItem(msg))
        self.inference_worker.progress_update.connect(self._update_infer_progress)
        self.inference_worker.finished.connect(self._on_infer_finished)
        self.inference_worker.evaluation_finished.connect(self._on_evaluation_finished)
        self.inference_worker.error.connect(self._on_infer_error)
        self.inference_worker.start()

    def _update_infer_progress(self, current, total):
        self.infer_progress.setRange(0, total)
        self.infer_progress.setValue(current)

    def _on_infer_finished(self, output_dir):
        self.btn_infer.setEnabled(True)
        self.infer_console.addItem(f"✅ 推理完成！结果保存在: {output_dir}")
        self.infer_console.scrollToBottom()

    def _on_evaluation_finished(self, report):
        dialog = EvaluationDialog(report, self)
        dialog.exec()

    def _on_infer_error(self, msg):
        self.btn_infer.setEnabled(True)
        self.infer_console.addItem(f"❌ 推理出错: {msg}")

    def validate_page(self) -> bool:
        return True # Step 5 is optional/final, no strict validation to proceed
