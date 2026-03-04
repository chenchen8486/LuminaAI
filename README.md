# LuminaAI - 深度学习视觉开发平台

![LuminaAI Banner](ui/picture/1.jpg)

**LuminaAI (VisionForge)** 是一个集成化的工业级深度学习视觉平台，专为快速构建、训练和部署计算机视觉模型而设计。它提供从数据标注、模型配置、训练监控到模型导出与评估的端到端解决方案，支持 **目标检测**、**图像分割** 和 **图像分类** 三大核心任务。

## ✨ 核心特性

- **多任务支持**：
  - 🎯 **目标检测 (Object Detection)**：基于 YOLOv8，精准识别物体位置与类别。
  - 🖌️ **图像分割 (Instance Segmentation)**：像素级抠图，支持复杂场景分割。
  - 🖼️ **图像分类 (Image Classification)**：基于 ResNet 等经典网络，快速整图识别。

- **智能数据管理**：
  - 内置 **LabelMe** 启动接口，无缝对接标注流程。
  - 自动生成分割掩码 (Mask)，支持数据完整性校验与统计。
  - 严格的数据隔离机制 (Raw / Annotations / Temp / Models)。

- **零代码训练向导**：
  - **可视化配置**：通过 GUI 调整 Epochs, Batch Size, Learning Rate 等超参数。
  - **实时监控**：动态绘制 Loss / mAP 曲线，实时查看训练日志。
  - **硬件自适应**：自动检测 GPU/CPU 资源，智能调度计算任务。

- **模型评估与部署**：
  - **批量推理**：支持文件夹级批量图片预测，自动生成可视化结果。
  - **多维评估**：自动计算 Precision, Recall, F1-Score, mAP 等关键指标。
  - **一键导出**：支持导出为 ONNX, TorchScript 等通用格式，适配多平台部署。

- **现代化 UI 设计**：
  - 采用 **Trae Style** 高对比度暗色主题。
  - 动态背景切换，沉浸式操作体验。
  - 响应式布局与清晰的操作指引。

## 🛠️ 技术栈

- **语言**: Python 3.10+
- **深度学习框架**: PyTorch, Ultralytics (YOLOv8)
- **图形界面**: PySide6 (Qt for Python)
- **图像处理**: OpenCV, Pillow, NumPy
- **打包工具**: PyInstaller

## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.10 或更高版本，并建议使用虚拟环境。

```bash
# 克隆项目
git clone https://github.com/your-repo/LuminaAI.git
cd LuminaAI

# 创建虚拟环境 (推荐)
python -m venv venv
# Windows 激活
venv\Scripts\activate
# Linux/Mac 激活
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行应用

```bash
python main.py
```

### 3. 打包发布 (可选)

生成独立的可执行文件 (.exe)：

```bash
pyinstaller LuminaAI.spec
```
打包完成后，程序位于 `dist/LuminaAI/LuminaAI.exe`。

## 📂 项目结构

```
LuminaAI/
├── core/                   # 核心算法模块
│   ├── data_management/    # 数据处理与转换
│   ├── training/           # 模型训练引擎
│   ├── inference/          # 推理与评估逻辑
│   └── export/             # 模型导出模块
├── ui/                     # 用户界面 (PySide6)
│   ├── wizards/            # 向导页逻辑 (Step 1-5)
│   ├── picture/            # UI 资源文件
│   └── styles.py           # 全局样式定义
├── data/                   # 数据存储目录 (自动生成)
├── docs/                   # 开发文档
├── requirements.txt        # 项目依赖
└── main.py                 # 程序入口
```

## 📚 开发文档

更多详细设计文档请参考 [docs/](docs/) 目录：
- [架构设计 (Architecture)](docs/01-architecture/architecture_design.md)
- [UI 设计规范](docs/03-ui-design/ui_resources.md)
- [模块设计](docs/02-module-design/)

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。
