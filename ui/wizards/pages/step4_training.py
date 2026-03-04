from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                               QTextEdit, QProgressBar, QHBoxLayout, QGroupBox, QMessageBox, QSplitter, QFrame)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QPixmap, QImage
from ui.wizards.base_wizard_page import BaseWizardPage
from core.training.trainer import TrainingWorker
from ui.styles import UIStyles
import os

class Step4Training(BaseWizardPage):
    def __init__(self, controller):
        super().__init__(controller)
        self.worker = None
        self.training_dir = None
        self.chart_timer = QTimer(self)
        self.chart_timer.timeout.connect(self._update_chart)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # --- Card Container ---
        # Since Step 4 is large, we might not want to center a small card.
        # But we still need a background to read text.
        # We'll make the whole page a "Card".
        
        self.card_frame = QFrame()
        self.card_frame.setObjectName("CardContainer")
        self.card_frame.setStyleSheet(UIStyles.CARD_CONTAINER)
        
        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Step 4: 模型训练与监控")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(UIStyles.LBL_TITLE)
        card_layout.addWidget(title)

        # Main Splitter (Left: Progress/Chart, Right: Log)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #444;
                width: 2px;
            }
        """)
        
        # Left Panel
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 10, 0)

        # Progress Section
        progress_group = QGroupBox("训练进度")
        progress_group.setStyleSheet(UIStyles.GROUP_BOX)
        progress_layout = QVBoxLayout(progress_group)
        
        self.lbl_epoch = QLabel("Epoch: 0 / 0")
        self.lbl_epoch.setStyleSheet(UIStyles.LBL_SUBTITLE)
        
        self.lbl_metrics = QLabel("Loss: - | mAP: -")
        self.lbl_metrics.setStyleSheet(f"color: {UIStyles.ACCENT_GREEN}; font-weight: bold; font-size: 14px;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(f"""
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
        
        progress_layout.addWidget(self.lbl_epoch)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.lbl_metrics)
        left_layout.addWidget(progress_group)
        
        # Chart Section
        chart_group = QGroupBox("实时指标 (Loss/Accuracy)")
        chart_group.setStyleSheet(UIStyles.GROUP_BOX)
        chart_layout = QVBoxLayout(chart_group)
        
        self.lbl_chart = QLabel("等待训练开始...")
        self.lbl_chart.setAlignment(Qt.AlignCenter)
        self.lbl_chart.setMinimumSize(400, 300)
        self.lbl_chart.setStyleSheet("background-color: rgba(0,0,0,0.3); border: 1px solid #444; color: #888;")
        chart_layout.addWidget(self.lbl_chart)
        left_layout.addWidget(chart_group)
        
        splitter.addWidget(left_widget)

        # Log Section (Right Panel)
        log_group = QGroupBox("训练日志")
        log_group.setStyleSheet(UIStyles.GROUP_BOX)
        log_layout = QVBoxLayout(log_group)
        
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet(f"background-color: #111; color: {UIStyles.TEXT_GRAY}; font-family: Consolas; border: 1px solid #333;")
        log_layout.addWidget(self.txt_log)
        splitter.addWidget(log_group)
        
        # Set splitter ratio (60% left, 40% right)
        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 4)
        card_layout.addWidget(splitter)

        # Control Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        
        self.btn_start = QPushButton("开始训练")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setStyleSheet(f"""
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
        self.btn_start.clicked.connect(self._start_training)
        
        self.btn_stop = QPushButton("停止训练")
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #dc3545; 
                color: white; 
                border: none;
                border-radius: 6px;
                font-weight: bold; 
                padding: 12px;
                font-size: 16px;
            }
            QPushButton:hover { background-color: #c82333; }
            QPushButton:disabled { background-color: #444; color: #666; }
        """)
        self.btn_stop.clicked.connect(self._stop_training)
        self.btn_stop.setEnabled(False)
        
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        card_layout.addLayout(btn_layout)
        
        layout.addWidget(self.card_frame)

    def _start_training(self):
        # Gather config from controller
        config = {
            "task_type": self.controller.get_data("task_type"),
            "dataset_path": self.controller.get_data("dataset_path"),
            "model_name": self.controller.get_data("model_name"),
            "epochs": self.controller.get_data("epochs"),
            "batch_size": self.controller.get_data("batch_size"),
            "workers": self.controller.get_data("workers"),
            "imgsz": self.controller.get_data("imgsz"),
            "lr0": self.controller.get_data("lr0"),
            "gpu_id": self.controller.get_data("gpu_id")
        }
        
        if not config["dataset_path"]:
            QMessageBox.warning(self, "错误", "未选择数据集路径，请返回 Step 2！")
            return

        self.txt_log.clear()
        self.txt_log.append(">>> 正在初始化训练任务...")
        self.lbl_chart.setText("正在初始化...")
        
        # Create Worker
        self.worker = TrainingWorker(config)
        self.worker.log_message.connect(self._append_log)
        self.worker.progress_update.connect(self._update_progress)
        self.worker.training_started.connect(self._on_training_started)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        
        self.worker.start()
        
        # Update UI state
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setValue(0)
        self.lbl_epoch.setText(f"Epoch: 0 / {config['epochs']}")

    def _stop_training(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.btn_stop.setEnabled(False)
            self.txt_log.append(">>> 正在停止...")
            self.chart_timer.stop()

    @Slot(str)
    def _on_training_started(self, output_dir):
        self.training_dir = output_dir
        self.chart_timer.start(5000) # Check every 5 seconds

    def _update_chart(self):
        if not self.training_dir:
            return
            
        # Try to find results.png
        chart_path = os.path.join(self.training_dir, "results.png")
        if os.path.exists(chart_path):
            pixmap = QPixmap(chart_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(self.lbl_chart.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.lbl_chart.setPixmap(scaled_pixmap)
            else:
                self.lbl_chart.setText("无法加载图表")
        else:
            self.lbl_chart.setText("等待生成图表 (results.png)...")

    @Slot(str)
    def _append_log(self, msg):
        self.txt_log.append(msg)
        # Auto scroll
        sb = self.txt_log.verticalScrollBar()
        sb.setValue(sb.maximum())

    @Slot(int, dict)
    def _update_progress(self, epoch, metrics):
        total_epochs = self.controller.get_data("epochs", 100)
        self.lbl_epoch.setText(f"Epoch: {epoch} / {total_epochs}")
        
        progress = int((epoch / total_epochs) * 100)
        self.progress_bar.setValue(progress)
        
        # Format metrics (simplified for demo)
        # We can extract loss/map from metrics dict
        self.lbl_metrics.setText(f"Metrics Updated: {metrics}")
        
        # Force update chart immediately on epoch end
        self._update_chart()

    @Slot(bool, str)
    def _on_finished(self, success, result):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.chart_timer.stop()
        self._update_chart() # Final update
        
        if success:
            QMessageBox.information(self, "完成", f"训练成功完成！\n模型保存在: {result}")
            self.controller.set_data("trained_model_path", result)
            # Enable next step (Step 5: Export)
            # Signal parent container?
        else:
            QMessageBox.warning(self, "失败", f"训练未完成: {result}")

    @Slot(str)
    def _on_error(self, err_msg):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.chart_timer.stop()
        self.txt_log.append(f"[ERROR] {err_msg}")
        QMessageBox.critical(self, "错误", err_msg)
