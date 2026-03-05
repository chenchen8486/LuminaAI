import os
import shutil
import logging
from pathlib import Path
from core.infrastructure.config_manager import config

logger = logging.getLogger(__name__)

class ProjectInitializer:
    """
    负责项目初始化，包括：
    1. 根据配置文件创建标准目录结构
    2. 迁移根目录下的残留文件 (如 .pt, runs/)
    """

    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else Path(os.getcwd())

    def execute(self):
        """执行初始化流程"""
        logger.info(">>> 开始项目初始化检查...")
        
        self._create_directories()
        self._migrate_legacy_files()
        
        logger.info("<<< 项目初始化完成。")

    def _create_directories(self):
        """动态创建配置文件中定义的所有关键路径"""
        # 从配置中获取关键路径列表
        paths_to_create = [
            "raw_data",
            "annotations",
            "temp_build",
            "models_pretrain",
            "models_export",
            "results_train",
            "results_inference",
            "logs_root",
            "configs_root"
        ]
        
        for key in paths_to_create:
            # 使用 config.get_path 自动处理绝对/相对路径
            abs_path_str = config.get_path(key)
            if abs_path_str:
                abs_path = Path(abs_path_str)
                if not abs_path.exists():
                    try:
                        abs_path.mkdir(parents=True, exist_ok=True)
                        (abs_path / ".gitkeep").touch()
                        logger.info(f"已创建目录: {abs_path}")
                    except Exception as e:
                        logger.error(f"创建目录失败 {abs_path}: {e}")

    def _migrate_legacy_files(self):
        """迁移根目录下的残留文件"""
        
        # 获取目标路径
        pretrain_dir = Path(config.get_path("models_pretrain"))
        results_dir = Path(config.get_path("results_train"))
        # 如果配置变了，这里逻辑要跟着变，或者只处理硬编码的旧位置
        # 为了鲁棒性，我们只处理根目录下“明显是旧文件”的东西
        
        # 1. 迁移根目录下的 .pt 模型
        if pretrain_dir.exists():
            for pt_file in self.base_dir.glob("*.pt"):
                try:
                    shutil.move(str(pt_file), str(pretrain_dir / pt_file.name))
                    logger.info(f"已迁移模型文件: {pt_file.name} -> {pretrain_dir}")
                except Exception as e:
                    logger.warning(f"迁移模型文件失败 {pt_file.name}: {e}")

        # 2. 迁移根目录下的 runs/ 文件夹
        legacy_runs = self.base_dir / "runs"
        
        # 这里的逻辑稍微复杂，如果用户改了 results_train 路径，我们还是要把 runs 移进去
        # 但要注意 legacy_runs 里的结构通常是 detect/train...
        # results_train 配置的可能是 data/05_results/train_runs
        
        if legacy_runs.exists() and legacy_runs.is_dir() and results_dir.exists():
            try:
                # 目标：将 runs/ 下的所有内容移动到 results_train 下
                # 避免嵌套过深，直接把 runs 下的子文件夹移过去
                for item in legacy_runs.iterdir():
                    dest = results_dir / item.name
                    if not dest.exists():
                        shutil.move(str(item), str(dest))
                    else:
                        # 冲突处理：如果目标存在，可能需要合并或改名
                        # 简单起见，如果重名就跳过或覆盖
                        logger.warning(f"目录已存在，跳过迁移: {dest}")
                
                # 尝试删除空的 legacy_runs
                try:
                    legacy_runs.rmdir()
                    logger.info("已清理空的 runs/ 目录")
                except:
                    pass # 可能还有非空文件
                    
            except Exception as e:
                logger.warning(f"迁移 runs/ 目录失败: {e}")

