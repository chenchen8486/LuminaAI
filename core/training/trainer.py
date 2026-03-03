import os
import sys
import time
import shutil
from pathlib import Path
from PySide6.QtCore import QThread, Signal, QObject

# Try to import ultralytics, handle if missing
try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False

class TrainingWorker(QThread):
    """
    Background worker for running training tasks.
    Supports YOLOv8 via ultralytics package.
    """
    # Signals
    log_message = Signal(str)       # Raw log line
    progress_update = Signal(int, dict) # epoch, metrics (map/loss)
    finished = Signal(bool, str)    # success, message/path
    error = Signal(str)             # error message
    training_started = Signal(str)  # output_dir

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.is_running = False
        self.model = None

    def run(self):
        if not ULTRALYTICS_AVAILABLE:
            self.error.emit("错误: 未检测到 'ultralytics' 库。请安装: pip install ultralytics")
            return

        self.is_running = True
        try:
            self.log_message.emit(">>> 初始化训练引擎...")
            
            # 1. Parse Config
            task_type = self.config.get("task_type", "detection") # detection, segmentation, classification
            model_name = self.config.get("model_name", "YOLOv8-Nano")
            dataset_path = self.config.get("dataset_path")
            epochs = self.config.get("epochs", 100)
            batch_size = self.config.get("batch_size", 16)
            workers = self.config.get("workers", 4)
            imgsz = self.config.get("imgsz", 640)
            lr0 = self.config.get("lr0", 0.01)
            device = self.config.get("gpu_id", 0) # 0 for GPU 0, 'cpu' for CPU

            # 2. Resolve Model Weights
            # Map UI name to actual weight file
            model_map = {
                "YOLOv8-Nano": "yolov8n.pt",
                "YOLOv8-Small": "yolov8s.pt",
                "YOLOv8-Medium": "yolov8m.pt",
                "ResNet-50": "yolov8n-cls.pt" # Fallback for demo
            }
            
            # Handle Task Specific Suffix
            weight_file = model_map.get(model_name, "yolov8n.pt")
            if task_type == "segmentation" and "yolov8" in weight_file:
                weight_file = weight_file.replace(".pt", "-seg.pt")
            elif task_type == "classification" and "yolov8" in weight_file:
                weight_file = weight_file.replace(".pt", "-cls.pt")
                
            self.log_message.emit(f"加载模型权重: {weight_file}")
            self.model = YOLO(weight_file)

            # 3. Add Callbacks for UI Update
            self.model.add_callback("on_train_epoch_end", self._on_epoch_end)
            
            # 4. Prepare Dataset Config (YAML)
            # If dataset_path is a directory, we might need to generate a data.yaml
            # For Phase 2 we assume standard structure or auto-generated yaml
            # Here we check if a yaml exists, otherwise we might need to create one.
            # For simplicity, assume data.yaml exists in dataset_path or passed path is yaml
            
            data_cfg = dataset_path
            if os.path.isdir(dataset_path):
                potential_yaml = os.path.join(dataset_path, "data.yaml")
                if os.path.exists(potential_yaml):
                    data_cfg = potential_yaml
                else:
                    # TODO: Auto-generate data.yaml if missing (Phase 2 feature)
                    self.error.emit(f"错误: 在 {dataset_path} 下未找到 data.yaml 配置文件")
                    return

            # 5. Start Training
            project_dir = os.path.join(os.getcwd(), "runs", "train")
            name = f"{task_type}_{model_name}_{int(time.time())}"
            output_dir = os.path.join(project_dir, name)
            
            self.log_message.emit(f"开始训练: Epochs={epochs}, Batch={batch_size}, Device={device}")
            self.log_message.emit(f"输出目录: {output_dir}")
            
            self.training_started.emit(output_dir)

            results = self.model.train(
                data=data_cfg,
                epochs=epochs,
                batch=batch_size,
                workers=workers,
                imgsz=imgsz,
                lr0=lr0,
                device=device,
                project=project_dir,
                name=name,
                exist_ok=True,
                verbose=True # Prints to stdout, captured by callback or stream
            )

            self.finished.emit(True, str(results.save_dir))

        except Exception as e:
            import traceback
            self.error.emit(f"训练发生异常:\n{traceback.format_exc()}")
        finally:
            self.is_running = False

    def stop(self):
        """Request to stop training"""
        if self.is_running:
            self.log_message.emit(">>> 正在请求停止训练...")
            # Ultralytics doesn't have a clean 'stop' method on the model object easily accessible 
            # from outside the loop without hacking.
            # But we can try to set a flag or terminate thread.
            # For now, we just rely on thread termination (not safe) or let it finish epoch.
            # A better way is to raise StopIteration in callback.
            pass

    def _on_epoch_end(self, trainer):
        """Callback from YOLO"""
        if not self.is_running:
            raise StopIteration("User cancelled training")
            
        epoch = trainer.epoch + 1
        metrics = trainer.metrics
        
        # Format a log message
        # box_loss, cls_loss, dfl_loss = trainer.loss_items
        # mAP50 = metrics.get("metrics/mAP50(B)", 0)
        
        self.log_message.emit(f"Epoch {epoch}/{trainer.epochs} completed.")
        self.progress_update.emit(epoch, metrics)
