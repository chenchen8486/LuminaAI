import os
import shutil
from typing import Optional
from PySide6.QtCore import QObject, Signal, QThread
from ultralytics import YOLO

class ExportWorker(QThread):
    """
    Worker thread for exporting YOLO models to different formats (ONNX, etc.)
    to prevent UI freezing.
    """
    progress_update = Signal(str)  # Emits progress messages
    export_finished = Signal(str)  # Emits the path to the exported model on success
    error_occurred = Signal(str)   # Emits error message on failure

    def __init__(self, model_path: str, format: str = 'onnx', imgsz: int = 640, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.model_path = model_path
        self.format = format
        self.imgsz = imgsz

    def run(self):
        try:
            self.progress_update.emit(f"正在加载模型: {self.model_path}...")
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"模型文件未找到: {self.model_path}")

            model = YOLO(self.model_path)
            
            self.progress_update.emit(f"开始导出为 {self.format.upper()} 格式 (imgsz={self.imgsz})...")
            
            # Ultralytics export returns the path to the exported file
            exported_path = model.export(format=self.format, imgsz=self.imgsz)
            
            if exported_path:
                # Move exported file to data/04_models/export
                export_dir = os.path.join(os.getcwd(), "data", "04_models", "export")
                os.makedirs(export_dir, exist_ok=True)
                
                filename = os.path.basename(exported_path)
                dest_path = os.path.join(export_dir, filename)
                
                # Check if file already exists in dest, handle overwrite or rename? 
                # shutil.move overwrites by default.
                try:
                    shutil.move(exported_path, dest_path)
                    final_path = dest_path
                    self.progress_update.emit(f"已归档导出模型至: {final_path}")
                except Exception as e:
                    self.progress_update.emit(f"警告: 归档失败，文件保留在原处: {exported_path} ({e})")
                    final_path = exported_path

                # Ensure the path is absolute
                abs_path = os.path.abspath(final_path)
                self.progress_update.emit("导出成功！")
                self.export_finished.emit(abs_path)
            else:
                raise RuntimeError("导出过程完成但未返回文件路径。")

        except Exception as e:
            error_msg = f"模型导出失败: {str(e)}"
            self.progress_update.emit(error_msg)
            self.error_occurred.emit(error_msg)

class ModelExporter:
    """
    Helper class to manage the export process, primarily for non-GUI usage or testing.
    """
    @staticmethod
    def export_model(model_path: str, format: str = 'onnx', imgsz: int = 640) -> str:
        """
        Synchronous export function.
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件未找到: {model_path}")

        model = YOLO(model_path)
        exported_path = model.export(format=format, imgsz=imgsz)
        return os.path.abspath(exported_path)
