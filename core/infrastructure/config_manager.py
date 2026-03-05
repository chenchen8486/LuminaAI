import os
import yaml
import threading
import logging
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class ConfigManager:
    _instance = None
    _lock = threading.Lock()
    _config = {}
    
    # 默认配置路径
    DEFAULT_CONFIG_DIR = "configs"
    DEFAULT_CONFIG_FILE = "config.yaml"

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConfigManager, cls).__new__(cls)
                    cls._instance._init_paths()
                    cls._instance._load_config()
        return cls._instance

    def _init_paths(self):
        """确保配置目录存在"""
        if not os.path.exists(self.DEFAULT_CONFIG_DIR):
            try:
                os.makedirs(self.DEFAULT_CONFIG_DIR)
            except Exception as e:
                logger.error(f"Failed to create config directory: {e}")

    def _load_config(self):
        config_path = os.path.join(self.DEFAULT_CONFIG_DIR, self.DEFAULT_CONFIG_FILE)
        
        # 默认配置模板 (更新版)
        default_config = {
            "system": {
                "language": "zh_CN", 
                "developer_mode": False,
                "theme": "dark"
            },
            # 增强路径配置：提供 data_root 和更详细的子目录配置
            "paths": {
                "root": ".",  # 根目录，默认为当前目录
                "data_root": "data",
                "configs_root": "configs",
                "logs_root": "logs",
                
                # Data 子目录
                "raw_data": "data/01_raw",
                "annotations": "data/02_annotations",
                "temp_build": "data/03_temp_build",
                
                # Models
                "models_root": "data/04_models",
                "models_pretrain": "data/04_models/pretrain",
                "models_export": "data/04_models/export",
                
                # Results
                "results_root": "data/05_results",
                "results_train": "data/05_results/train_runs",
                "results_inference": "data/05_results/inference"
            },
            "training": {
                "default_epochs": 100,
                "default_batch_size": 16,
                "auto_download_weights": True # 是否允许自动下载权重
            }
        }

        if not os.path.exists(config_path):
            self._config = default_config
            self._save_config() # 首次生成默认配置
            return

        try:
            with open(config_path, 'r', encoding='utf-8-sig') as f:
                loaded_config = yaml.safe_load(f) or {}
                # 简单的合并逻辑，确保新字段被合入
                self._recursive_update(default_config, loaded_config)
                self._config = default_config
                # Save the merged config back to disk to ensure new defaults are visible
                self._save_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._config = default_config

    def _recursive_update(self, d, u):
        """递归更新字典，保留默认值中存在但文件中缺失的字段"""
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = self._recursive_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    def get(self, key, default=None):
        """
        Get config value by dot-separated key, e.g. 'paths.raw_data'
        """
        keys = key.split('.')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
            
    def get_path(self, key):
        """
        专门用于获取路径，会自动处理相对路径和绝对路径。
        如果配置的是相对路径，会基于 os.getcwd() 转换为绝对路径。
        """
        path_str = self.get(f"paths.{key}")
        if not path_str:
            return None
        
        # 简单判断是否绝对路径，如果不是则拼接 cwd
        # 注意：这里假设所有 path 都是相对于项目根目录的
        path_obj = Path(path_str)
        if path_obj.is_absolute():
            return str(path_obj)
        else:
            return str(Path(os.getcwd()) / path_obj)

    def set(self, key, value):
        """
        Set config value by dot-separated key and save to file
        """
        keys = key.split('.')
        config_section = self._config
        for k in keys[:-1]:
            config_section = config_section.setdefault(k, {})
        config_section[keys[-1]] = value
        self._save_config()

    def _save_config(self):
        config_path = os.path.join(self.DEFAULT_CONFIG_DIR, self.DEFAULT_CONFIG_FILE)
        try:
            with open(config_path, 'w', encoding='utf-8-sig') as f:
                yaml.dump(self._config, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

# Global instance
config = ConfigManager()
