from PySide6.QtCore import QObject, Signal

class WizardController(QObject):
    # Signals
    page_changed = Signal(int)  # Emits current page index
    data_changed = Signal(str, object)  # key, value
    wizard_finished = Signal()

    def __init__(self):
        super().__init__()
        self._init_data()

    def _init_data(self):
        self._data = {
            "task_type": None,  # detection, segmentation, classification
            "dataset_path": None,
            "model_name": None,
            "epochs": 100,
            "batch_size": 16,
            "gpu_id": 0,
            # Advanced Hyperparameters
            "lr0": 0.01,
            "imgsz": 640,
            "workers": 4,
            
            # Dataset Statistics
            "dataset_stats": None,
            
            # Training Result
            "trained_model_path": None
        }
        self._current_step = 0
        self._total_steps = 5

    def set_data(self, key, value):
        self._data[key] = value
        self.data_changed.emit(key, value)
        # TODO: Log data change
        
    def get_data(self, key, default=None):
        return self._data.get(key, default)

    def validate_current_step(self):
        """
        Validates the current step's data.
        Returns: (bool, str) -> (is_valid, error_message)
        """
        if self._current_step == 0:
            if not self._data.get("task_type"):
                return False, "请先选择一个任务类型（目标检测/图像分割/图像分类）！"
        
        elif self._current_step == 1:
            if not self._data.get("dataset_path"):
                return False, "请先选择数据文件夹！"
                
        elif self._current_step == 3: # Training Step
            if not self._data.get("trained_model_path"):
                return False, "请先完成模型训练！"

        # Step 2 (Model Params) usually has defaults, so it might be always valid
        # unless we add specific constraints later.
        
        return True, ""

    def next_step(self):
        if self._current_step < self._total_steps - 1:
            self._current_step += 1
            self.page_changed.emit(self._current_step)
    
    def prev_step(self):
        if self._current_step > 0:
            self._current_step -= 1
            self.page_changed.emit(self._current_step)

    def reset(self):
        self._init_data()
        self.page_changed.emit(0)

wizard_controller = WizardController()
