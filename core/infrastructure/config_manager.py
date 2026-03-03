import os
import yaml
import threading

class ConfigManager:
    _instance = None
    _lock = threading.Lock()
    _config = {}

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConfigManager, cls).__new__(cls)
                    cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        config_path = os.path.join("configs", "config.yaml")
        if not os.path.exists(config_path):
            # Fallback default
            self._config = {
                "system": {"language": "zh_CN", "developer_mode": False},
                "training": {"default_epochs": 100}
            }
            return

        with open(config_path, 'r', encoding='utf-8-sig') as f:
            self._config = yaml.safe_load(f)

    def get(self, key, default=None):
        """
        Get config value by dot-separated key, e.g. 'system.language'
        """
        keys = key.split('.')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

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
        config_path = os.path.join("configs", "config.yaml")
        with open(config_path, 'w', encoding='utf-8-sig') as f:
            yaml.dump(self._config, f, allow_unicode=True)

# Global instance
config = ConfigManager()
