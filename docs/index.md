# LuminaAI 全局开发路线图

## 项目总览
本项目严格遵循 **渐进式开发 (Sequential Development)** 模式。每个 Phase 完成并经过验证后，方可进入下一 Phase。

## 📅 Phase 1: 基础架构与 UI 框架 (Infrastructure & UI Framework)
- **目标**：搭建 PySide6 主窗口框架，实现向导模式的基础交互，确立配置管理机制。
- **核心任务**：
    - [x] 建立 `core/infrastructure` (Config, Log, PathUtils)。
    - [x] 搭建 PySide6 主界面 (`MainWindow`) 与 导航栏。
    - [x] 实现 Step 1 (任务选择) 至 Step 3 (参数设置) 的 UI 流程（无实际后端逻辑）。
    - [x] 实现 `WizardController` 用于管理向导状态。

## 📅 Phase 2: 数据管理与标注引擎 (Data Management & Labeling)
- **目标**：打通数据流，实现图片导入、格式转换与标注功能。
- **核心任务**：
    - [x] 实现 `DataManager`：文件扫描、校验、数据集划分 (Train/Val)。
    - [x] 开发/集成 格式转换脚本 (LabelMe <-> VOC <-> YOLO)。
    - [x] 集成 LabelMe 或开发简易 Canvas，实现 `Step 2` 的完整逻辑。
    - [x] 生成二值化 Mask 功能实现。

## 📅 Phase 3: 模型训练引擎 (Training Engine)
- **目标**：实现多进程训练循环，打通 UI 监控。
- **核心任务**：
    - [ ] 封装 PyTorch `Dataset` 和 `DataLoader`。
    - [ ] 实现 `TrainingWorker` (QThread/Multiprocessing)，处理训练循环。
    - [ ] 对接 UI 实时绘图 (Loss/LR 曲线) 与 进度条 (ETA)。
    - [ ] 实现“高级设置”与 YAML 配置文件的双向绑定。

## 📅 Phase 4: 推理评估与导出 (Inference, Eval & Export)
- **目标**：实现模型验证、过漏检分析及工业级导出。
- **核心任务**：
    - [ ] 开发批量推理引擎 (`InferenceEngine`)。
    - [ ] 实现过漏检统计逻辑 (FP/FN Calculation)。
    - [ ] 开发结果可视化界面 (BBox/Mask Overlay)。
    - [ ] 集成 ONNX 导出功能 (`Step 5`)。

## 📅 Phase 5: 打包与交付 (Distribution)
- **目标**：生成稳定可用的 `.exe` 安装包。
- **核心任务**：
    - [ ] 配置 `PyInstaller` spec 文件，处理 hidden-imports。
    - [ ] 验证 GPU/CPU 自动切换在打包环境下的有效性。
    - [ ] 编写用户手册与最终验收测试。

---
*Last Updated: 2026-03-03*
