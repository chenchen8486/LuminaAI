from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QGroupBox, QFormLayout, QMessageBox, QHBoxLayout
from PySide6.QtCore import Qt, QThread, Signal
from ui.wizards.base_wizard_page import BaseWizardPage
from core.data_management.data_manager import DataManager
from core.data_management.format_converter import FormatConverter
import subprocess
import shutil

class ScanWorker(QThread):
    finished = Signal(dict)
    
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.data_manager = DataManager()

    def run(self):
        stats = self.data_manager.scan_directory(self.path)
        self.finished.emit(stats)

class Step2DataImport(BaseWizardPage):
    def __init__(self, controller):
        super().__init__(controller)
        self.scan_worker = None

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("Step 2: 数据导入与校验")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Path Display
        self.lbl_path = QLabel("未选择文件夹")
        self.lbl_path.setAlignment(Qt.AlignCenter)
        self.lbl_path.setStyleSheet("color: #888; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(self.lbl_path)

        # Select Button
        btn_select = QPushButton("选择数据文件夹")
        btn_select.setFixedSize(200, 50)
        btn_select.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #009ce0;
            }
        """)
        btn_select.clicked.connect(self._open_folder_dialog)
        layout.addWidget(btn_select, alignment=Qt.AlignCenter)
        
        # Statistics Group
        self.stats_group = QGroupBox("数据集概览")
        self.stats_group.setFixedWidth(400)
        self.stats_group.setVisible(False)
        stats_layout = QFormLayout(self.stats_group)
        
        self.lbl_total_images = QLabel("0")
        self.lbl_total_anns = QLabel("0")
        self.lbl_classes = QLabel("-")
        self.lbl_missing = QLabel("0")
        
        stats_layout.addRow("图片总数:", self.lbl_total_images)
        stats_layout.addRow("标注文件数:", self.lbl_total_anns)
        stats_layout.addRow("识别类别:", self.lbl_classes)
        stats_layout.addRow("缺失标注:", self.lbl_missing)
        
        layout.addWidget(self.stats_group, alignment=Qt.AlignCenter)
        
        # --- Tools Section ---
        self.tools_group = QGroupBox("标注与转换工具")
        self.tools_group.setFixedWidth(400)
        self.tools_group.setVisible(False)
        tools_layout = QHBoxLayout(self.tools_group)
        
        self.btn_labelme = QPushButton("启动 LabelMe")
        self.btn_labelme.clicked.connect(self._launch_labelme)
        
        self.btn_gen_mask = QPushButton("生成掩码 (Mask)")
        self.btn_gen_mask.clicked.connect(self._generate_masks)
        
        tools_layout.addWidget(self.btn_labelme)
        tools_layout.addWidget(self.btn_gen_mask)
        
        layout.addWidget(self.tools_group, alignment=Qt.AlignCenter)
        # ---------------------
        
        # Loading Indicator
        self.lbl_loading = QLabel("正在扫描数据集...")
        self.lbl_loading.setVisible(False)
        self.lbl_loading.setStyleSheet("color: #007acc; font-weight: bold;")
        layout.addWidget(self.lbl_loading, alignment=Qt.AlignCenter)

    def _open_folder_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "选择数据目录")
        if folder:
            self.lbl_path.setText(folder)
            self.controller.set_data("dataset_path", folder)
            self._start_scan(folder)

    def _start_scan(self, path):
        self.stats_group.setVisible(False)
        self.tools_group.setVisible(False)
        self.lbl_loading.setVisible(True)
        
        self.scan_worker = ScanWorker(path)
        self.scan_worker.finished.connect(self._on_scan_finished)
        self.scan_worker.start()

    def _on_scan_finished(self, stats):
        self.lbl_loading.setVisible(False)
        if not stats:
            QMessageBox.warning(self, "错误", "无法读取该目录或目录为空！")
            return
            
        self.controller.set_data("dataset_stats", stats)
        
        # Update UI
        self.lbl_total_images.setText(str(stats["total_images"]))
        self.lbl_total_anns.setText(str(stats["total_annotations"]))
        
        classes = list(stats["classes"].keys())
        class_text = ", ".join(classes) if classes else "无"
        if len(class_text) > 30:
            class_text = class_text[:30] + "..."
        self.lbl_classes.setText(class_text)
        self.lbl_classes.setToolTip(", ".join(classes))
        
        self.lbl_missing.setText(str(stats["missing_annotations"]))
        if stats["missing_annotations"] > 0:
            self.lbl_missing.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.lbl_missing.setStyleSheet("color: green;")
            
        self.stats_group.setVisible(True)
        self.tools_group.setVisible(True)

    def _launch_labelme(self):
        # Check if labelme is installed
        if shutil.which("labelme"):
            try:
                path = self.controller.get_data("dataset_path")
                subprocess.Popen(["labelme", path])
            except Exception as e:
                 QMessageBox.warning(self, "错误", f"启动 LabelMe 失败: {e}")
        else:
            QMessageBox.warning(self, "提示", "未检测到 'labelme' 命令。请先安装: pip install labelme")

    def _generate_masks(self):
        path = self.controller.get_data("dataset_path")
        if not path:
            return
            
        from pathlib import Path
        json_files = list(Path(path).glob("*.json"))
        if not json_files:
            QMessageBox.information(self, "提示", "未找到 JSON 标注文件。")
            return
            
        count = 0
        for json_file in json_files:
            if FormatConverter.json_to_mask(json_file, path):
                count += 1
                
        QMessageBox.information(self, "完成", f"已成功生成 {count} 个掩码文件！")
        # Rescan to update stats
        self._start_scan(path)
