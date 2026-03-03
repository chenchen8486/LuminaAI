# EasyVision Studio 架构设计文档

## 1. 技术选型分析与建议

### 1.1 GUI 框架选型对比

针对“本地运行、重计算、易打包”的核心需求，对比分析如下：

| 特性 | **PySide6 (Qt for Python)** | **Electron + Python** | **Tauri + Python** |
| :--- | :--- | :--- | :--- |
| **架构模式** | Native Python Binding | Web Frontend + Node.js + Python Backend | Web Frontend + Rust Core + Python Sidecar |
| **性能体验** | **高** (原生渲染，内存占用适中) | 中 (Chromium 内核内存占用高) | 高 (使用系统 WebView) |
| **Python 集成** | **无缝** (同进程/直接调用) | 需通过 HTTP/Socket 通信 (有序列化开销) | 需通过 Command/Sidecar 通信 (复杂) |
| **重计算支持** | 优秀 (QThread/Multiprocessing 易控制) | 需通过 IPC 异步调用，流程割裂 | 需通过 Rust 桥接，调试困难 |
| **打包难度** | **低** (PyInstaller/Nuitka 成熟) | **高** (需打包 Node, Python 环境并处理通信) | **极高** (Python 环境需独立打包并配置 Sidecar) |
| **开发效率** | 中 (需学习 Qt API, QSS 美化) | 高 (HTML/CSS 现代化 UI 容易实现) | 中 (需懂 Rust 基础配置) |

#### 🚀 最终建议：**PySide6 (Qt)**
*   **理由**：
    1.  **数据零拷贝**：深度学习任务涉及大量图像/Tensor 数据。PySide6 可以直接将 numpy array 转为 QImage 显示，无需像 Electron 那样进行 Base64 编码/解码或 HTTP 传输，这对于实时推理预览至关重要。
    2.  **打包稳定性**：PyInstaller 对 PySide6 支持极佳，生成的单文件 EXE 稳定性远高于“浏览器+服务器”的组合架构。
    3.  **开发一致性**：全栈 Python，无需维护 JS/TS 代码，降低团队技术栈分裂风险。
    4.  **生态**：Qt 的 `Graphics View Framework` 非常适合做复杂的图像标注工具（类似 LabelMe）。

### 1.2 后端/计算架构选型

| 方案 | **纯 Python (Multiprocessing)** | **FastAPI 本地服务** |
| :--- | :--- | :--- |
| **通信方式** | 共享内存 / Queue / Pipe | HTTP REST API / WebSocket |
| **部署复杂度** | 低 (单一进程树) | 中 (需管理端口、进程守护) |
| **数据传输** | **快** (内存级) | 慢 (JSON 序列化/反序列化) |
| **适用场景** | 紧密集成的桌面应用 | 需同时支持 Web/Desktop 的应用 |

#### 🚀 最终建议：**纯 Python + Multiprocessing**
*   **理由**：训练任务是计算密集型（CPU/GPU 阻塞），必须放在独立进程。使用 Python 标准库的 `multiprocessing` 配合 PySide6 的 `QThread` (用于非阻塞 UI 更新) 是标准做法。FastAPI 会引入不必要的网络层开销和端口冲突风险。

---

## 2. 项目目录结构设计

采用 **模块化插件式架构**，支持用户自定义模型和扩展。

```text
EasyVisionStudio/
├── configs/                # 全局与默认配置
│   ├── system_config.yaml  # 软件系统配置 (路径, 显卡, 语言)
│   └── default_hyper.yaml  # 默认超参数模版
├── core/                   # 核心业务逻辑 (与 UI 解耦)
│   ├── engine/             # 训练与推理引擎
│   │   ├── trainer_base.py # 训练器基类 (多进程封装)
│   │   ├── infer_base.py   # 推理器基类
│   │   └── task_manager.py # 任务调度 (管理训练队列)
│   ├── models/             # 模型定义 (支持动态加载)
│   │   ├── __init__.py     # 工厂模式模型加载器
│   │   ├── yolo_v8/        # 内置模型
│   │   └── custom_loader.py# 用户自定义代码加载逻辑
│   ├── data/               # 数据处理
│   │   ├── dataset.py      # PyTorch Dataset 封装
│   │   ├── transforms.py   # 增强 (Albumentations)
│   │   └── importer.py     # 数据集导入与格式转换
│   └── export/             # 模型导出
│       ├── onnx_exporter.py
│       └── tensorrt_exporter.py
├── ui/                     # 界面层 (PySide6)
│   ├── resources/          # 图标、样式表 (qss)
│   ├── widgets/            # 通用组件 (ImageCanvas, LogConsole)
│   ├── wizards/            # 向导模式组件 (NewTaskWizard)
│   ├── pages/              # 主功能页 (LabelPage, TrainPage)
│   └── main_window.py      # 主窗口框架
├── user_workspace/         # (运行时生成) 用户工作区
│   ├── models/             # 用户导入的 external models
│   └── projects/           # 具体项目数据
├── utils/                  # 工具库
│   ├── logger.py           # 日志系统
│   └── hardware.py         # GPU/CPU 检测
├── main.py                 # 启动入口
└── requirements.txt        # 依赖列表
```

---

## 3. 核心依赖列表 (requirements.txt)

```text
# GUI Framework
PySide6>=6.5.0          # 现代化 Qt6 绑定
qdarktheme>=2.1.0       # 现代化暗黑主题 (让 Qt 不再丑)

# Deep Learning Base
torch>=2.0.0            # 推荐 2.0+ 具备编译加速
torchvision>=0.15.0
torchaudio
--index-url https://download.pytorch.org/whl/cu118  # 需根据环境动态调整

# Data Processing & Augmentation
numpy>=1.24.0
pandas>=2.0.0           # 数据分析/表格
opencv-python-headless>=4.7.0  # 图像处理 (Headless 避免与 Qt 冲突)
pillow>=9.5.0
albumentations>=1.3.0   # 工业级数据增强
scikit-learn>=1.2.0     # 评估指标 (Confusion Matrix 等)

# Visualization
matplotlib>=3.7.0       # 绘图后端

# Model Export & Inference
onnx>=1.14.0
onnxruntime-gpu>=1.15.0 # 推理加速

# System & Utilities
pyyaml>=6.0             # 配置文件
tqdm>=4.65.0            # 进度条
psutil>=5.9.0           # 系统资源监控
```

## 4. 关键架构设计点

1.  **自定义模型导入机制**：
    *   约定接口：用户提供的 Python 文件必须包含一个继承自 `BaseModel` 的类，或提供一个 `get_model(num_classes, **kwargs)` 函数。
    *   实现：使用 `importlib.util.spec_from_file_location` 动态加载用户选定的 `.py` 文件，并注入到模型注册表中。

2.  **向导模式 (Wizard Mode)**：
    *   使用 `QWizard` 或自定义的分步堆叠组件 (`QStackedWidget`)。
    *   流程：选择任务类型 (检测/分割) -> 导入数据文件夹 (自动校验格式) -> 选择基础模型 (ResNet/YOLO) -> 设置显卡与 BatchSize -> 开始。

3.  **训练进程隔离**：
    *   UI 线程 **绝对不能** 运行训练循环。
    *   设计 `TrainingWorker(multiprocessing.Process)`。
    *   通信：`Queue` 用于发送 Loss/Accuracy 实时数据给 UI；`Event` 用于控制 暂停/停止。

4.  **标注工具集成**：
    *   初期不建议从零开发复杂标注工具。
    *   方案 A：内嵌 `labelme` (它是 Python 编写的，Qt 界面，易于集成)。
    *   方案 B：开发简化版 Canvas，只支持矩形框 (检测) 和 多边形 (分割)，满足轻量级需求。
