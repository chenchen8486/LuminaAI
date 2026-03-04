from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QGroupBox, 
    QFormLayout, QMessageBox, QHBoxLayout, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal
from ui.wizards.base_wizard_page import BaseWizardPage
from core.data_management.data_manager import DataManager
from core.data_management.format_converter import FormatConverter
from ui.styles import UIStyles
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
        layout.setContentsMargins(40, 20, 40, 20)
        
        # --- Main Card Container ---
        # Instead of global fog, we use a central "Card" for this step
        self.card_frame = QFrame()
        self.card_frame.setObjectName("CardContainer")
        self.card_frame.setStyleSheet(UIStyles.CARD_CONTAINER)
        self.card_frame.setFixedWidth(600) # Limit width for better look
        
        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(30, 40, 30, 40)
        card_layout.setSpacing(20)
        
        # Title
        title = QLabel("Step 2: 数据导入与校验")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(UIStyles.LBL_TITLE)
        card_layout.addWidget(title)
        
        # Path Display
        self.lbl_path = QLabel("未选择文件夹")
        self.lbl_path.setAlignment(Qt.AlignCenter)
        self.lbl_path.setWordWrap(True)
        self.lbl_path.setStyleSheet(UIStyles.LBL_SUBTITLE)
        card_layout.addWidget(self.lbl_path)

        # Select Button (Primary Action)
        btn_select = QPushButton("选择数据文件夹")
        btn_select.setCursor(Qt.PointingHandCursor)
        btn_select.setStyleSheet(f"""
            QPushButton {{
                background-color: {UIStyles.ACCENT_GREEN};
                color: {UIStyles.TEXT_BLACK};
                border: none;
                border-radius: 8px;
                font-family: "{UIStyles.FONT_FAMILY}";
                font-size: 18px;
                font-weight: bold;
                padding: 15px 40px;
            }}
            QPushButton:hover {{
                background-color: {UIStyles.ACCENT_HOVER};
            }}
        """)
        btn_select.clicked.connect(self._open_folder_dialog)
        card_layout.addWidget(btn_select, alignment=Qt.AlignCenter)
        
        # Statistics Group
        self.stats_group = QGroupBox("数据集概览")
        self.stats_group.setVisible(False)
        self.stats_group.setStyleSheet(UIStyles.GROUP_BOX)
        
        stats_layout = QFormLayout(self.stats_group)
        stats_layout.setLabelAlignment(Qt.AlignLeft)
        stats_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        stats_layout.setSpacing(10)
        
        label_style = f"color: {UIStyles.TEXT_GRAY}; font-size: 14px;"
        value_style = f"color: {UIStyles.TEXT_WHITE}; font-size: 14px; font-weight: bold;"
        
        def create_stat_row(label_text, value_widget):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            value_widget.setStyleSheet(value_style)
            return lbl, value_widget

        self.lbl_total_images = QLabel("0")
        self.lbl_total_anns = QLabel("0")
        self.lbl_classes = QLabel("-")
        self.lbl_missing = QLabel("0")
        
        l1, v1 = create_stat_row("图片总数:", self.lbl_total_images)
        stats_layout.addRow(l1, v1)
        
        l2, v2 = create_stat_row("标注文件数:", self.lbl_total_anns)
        stats_layout.addRow(l2, v2)
        
        l3, v3 = create_stat_row("识别类别:", self.lbl_classes)
        stats_layout.addRow(l3, v3)
        
        l4, v4 = create_stat_row("缺失标注:", self.lbl_missing)
        stats_layout.addRow(l4, v4)
        
        card_layout.addWidget(self.stats_group)
        
        # --- Tools Section ---
        self.tools_group = QGroupBox("标注与转换工具")
        self.tools_group.setVisible(False)
        self.tools_group.setStyleSheet(UIStyles.GROUP_BOX)
        
        tools_layout = QHBoxLayout(self.tools_group)
        tools_layout.setSpacing(15)
        
        self.btn_labelme = QPushButton("启动 LabelMe")
        self.btn_labelme.setCursor(Qt.PointingHandCursor)
        self.btn_labelme.setStyleSheet(UIStyles.BTN_SECONDARY)
        self.btn_labelme.clicked.connect(self._launch_labelme)
        
        self.btn_gen_mask = QPushButton("生成掩码 (Mask)")
        self.btn_gen_mask.setCursor(Qt.PointingHandCursor)
        self.btn_gen_mask.setStyleSheet(UIStyles.BTN_SECONDARY)
        self.btn_gen_mask.clicked.connect(self._generate_masks)
        
        tools_layout.addWidget(self.btn_labelme)
        tools_layout.addWidget(self.btn_gen_mask)
        
        card_layout.addWidget(self.tools_group)
        
        # Loading Indicator
        self.lbl_loading = QLabel("正在扫描数据集...")
        self.lbl_loading.setVisible(False)
        self.lbl_loading.setAlignment(Qt.AlignCenter)
        self.lbl_loading.setStyleSheet(f"color: {UIStyles.ACCENT_GREEN}; font-size: 16px; font-weight: bold; margin-top: 10px;")
        card_layout.addWidget(self.lbl_loading)
        
        # Add card to main layout
        layout.addWidget(self.card_frame, alignment=Qt.AlignCenter)

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
        # Use sys.executable to ensure we use the labelme installed in the current environment
        import sys
        
        try:
            path = self.controller.get_data("dataset_path")
            cmd = [sys.executable, "-m", "labelme"]
            if path:
                cmd.append(path)
                
            subprocess.Popen(cmd)
        except Exception as e:
             QMessageBox.warning(self, "错误", f"启动 LabelMe 失败: {e}\n请尝试手动运行 'pip install labelme'")

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
