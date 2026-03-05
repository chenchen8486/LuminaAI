import os
import sys
import time
import shutil
from pathlib import Path
from PySide6.QtCore import QThread, Signal, QObject
from core.data_management.format_converter import FormatConverter

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
            base_weight_name = model_map.get(model_name, "yolov8n.pt")
            if task_type == "segmentation" and "yolov8" in base_weight_name:
                base_weight_name = base_weight_name.replace(".pt", "-seg.pt")
            elif task_type == "classification" and "yolov8" in base_weight_name:
                base_weight_name = base_weight_name.replace(".pt", "-cls.pt")
            
            # Look for weights in data/04_models/pretrain first, then root
            pretrain_dir = os.path.join(os.getcwd(), "data", "04_models", "pretrain")
            os.makedirs(pretrain_dir, exist_ok=True)
            
            weight_file = os.path.join(pretrain_dir, base_weight_name)
            if not os.path.exists(weight_file):
                # Check if exists in root, move to pretrain
                root_weight = os.path.join(os.getcwd(), base_weight_name)
                if os.path.exists(root_weight):
                    shutil.move(root_weight, weight_file)
                    self.log_message.emit(f"已将权重移动到模型库: {weight_file}")
                else:
                    # If completely missing, let YOLO download.
                    # We will pass the name, YOLO downloads to CWD, then we move it.
                    weight_file = base_weight_name 

            if os.path.exists(os.path.join(pretrain_dir, base_weight_name)):
                 weight_file = os.path.join(pretrain_dir, base_weight_name)

            self.log_message.emit(f"加载模型权重: {weight_file}")
            self.model = YOLO(weight_file)
            
            # If YOLO downloaded it to root during init, move it to pretrain
            if weight_file == base_weight_name and os.path.exists(base_weight_name):
                 try:
                     shutil.move(base_weight_name, os.path.join(pretrain_dir, base_weight_name))
                     self.log_message.emit(f"自动归档预训练模型至: {pretrain_dir}")
                 except Exception as e:
                     self.log_message.emit(f"警告: 无法归档模型文件: {e}")

            # 3. Add Callbacks for UI Update
            self.model.add_callback("on_train_epoch_end", self._on_epoch_end)
            
            # 4. Prepare Dataset Config (YAML)
            data_cfg = dataset_path
            if os.path.isdir(dataset_path):
                potential_yaml = os.path.join(dataset_path, "data.yaml")
                if os.path.exists(potential_yaml):
                    data_cfg = potential_yaml
                else:
                    # Auto-generate data.yaml and convert dataset
                    self.log_message.emit(f"未找到 data.yaml，正在尝试自动转换数据集...")
                    try:
                        timestamp = int(time.time())
                        # Build temp path: data/03_temp_build/build_{timestamp}
                        temp_dir = os.path.join(os.getcwd(), "data", "03_temp_build", f"build_{timestamp}")
                        os.makedirs(temp_dir, exist_ok=True)
                        
                        self.log_message.emit(f"构建临时数据集: {temp_dir}")
                        # Call FormatConverter to split dataset and generate yaml
                        yaml_path = FormatConverter.prepare_yolo_dataset(dataset_path, temp_dir)
                        data_cfg = yaml_path
                        self.log_message.emit(f"数据集转换成功: {yaml_path}")
                        
                    except Exception as e:
                        import traceback
                        self.error.emit(f"自动转换数据集失败: {str(e)}\n{traceback.format_exc()}")
                        return

            # 5. Start Training
            # Change project_dir to data/05_results/train_runs to keep root clean
            project_dir = os.path.join(os.getcwd(), "data", "05_results", "train_runs")
            
            # Allow user to specify task name via config or auto-generate
            # For now, we stick to auto-gen but meaningful
            task_name = self.config.get("task_name", f"{task_type}_{model_name}")
            run_name = f"{task_name}_{int(time.time())}"
            
            output_dir = os.path.join(project_dir, run_name)
            
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
                project=project_dir, # Root dir for runs
                name=run_name,       # Subfolder name
                exist_ok=True,
                verbose=True 
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
