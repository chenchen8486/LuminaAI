# LuminaAI 详细使用说明书

本文档将指导您从零开始使用 LuminaAI 平台，详细说明数据准备、训练流程、模型管理及二次开发扩展等内容。

---

## 1. 数据准备与标注 (Step 1 & 2)

### 📂 目录结构建议
虽然软件支持任意目录，但为了方便管理，建议遵循以下结构：
```
LuminaAI/
├── data/
│   ├── 01_raw/             # [工作区] 存放原始图片 + LabelMe 标注的 JSON 文件
│   ├── 02_annotations/     # [归档区] (可选) 存放整理后的 XML/TXT 文件
│   ├── 04_models/          # [模型仓库]
│   │   ├── pretrain/       #    ├── 预训练权重 (yolov8n.pt 等)
│   │   └── export/         #    └── 导出模型 (.onnx, .engine 等)
│   ├── 05_results/         # [输出] 训练日志与结果
│   └── ...
```

### 🏷️ LabelMe 标注常见问题 (FAQ)

**Q1: 标注生成的 JSON 文件应该存在哪里？**
> **A: 请直接保存在图片所在的文件夹（例如 `01_raw`）。**
> *   **原因**：LuminaAI 的数据扫描引擎 (`Step 2`) 默认会在图片同级目录下查找同名的 `.json` 文件。如果分开存放，软件将无法自动关联图片与标注。
> *   **解决您的困扰**：LabelMe 默认会将 JSON 保存到图片当前目录。如果您不需要频繁切换输出目录，只需在 LabelMe 中点击 `File` -> `Save Automatically` (自动保存)，这样每次点击下一张时，它会自动在当前文件夹生成 JSON，**无需每次手动选择路径**。

**Q2: 既然都在 `01_raw`，那 `02_annotations` 有什么用？**
> **A:** `02_annotations` 是为您预留的**归档目录**。
> *   **纯标注归档**：当您完成所有标注并确认为“最终版”后，可以手动将 `.json` 移动到这里备份。
> *   **格式转换结果**：如果您使用了额外的脚本将 JSON 批量转换为 YOLO `.txt` 或 VOC `.xml` 格式，建议将这些生成的纯标注文件存放在 `02` 目录，以保持 `01` 目录（图片源）的清爽。但在**训练前的准备阶段**，建议保持“图片+标注”在一起。

---

## 2. 模型训练与配置 (Step 3 & 4)

### 🤖 预训练模型 (Pre-trained Models)

**Q: 预训练模型放在哪里？需要我手动下载吗？**
> **A: 不需要手动下载，系统会自动管理并分类存储。**
> *   **存放位置**：所有预训练权重（如 `yolov8n.pt`）会自动存放在 **`data/04_models/pretrain/`** 目录下。
> *   **自动归档**：如果您之前将权重文件放在了根目录，系统启动训练时会自动将其移动到 `pretrain` 目录，保持根目录整洁。
> *   **手动存放**：离线环境下，您可以直接将下载好的权重文件放入 `data/04_models/pretrain/`。

### 📤 模型导出 (Model Export)
**Q: 导出的 ONNX 模型去哪了？**
> **A:** 导出的模型文件（.onnx, .torchscript 等）会自动归档到 **`data/04_models/export/`** 目录中。

### ⚙️ 配置文件
目前训练参数主要通过 GUI 界面配置（Step 3）。底层的模型架构配置（YAML）由 `ultralytics` 库内置管理，您通常无需修改。

---

## 3. 二次开发与扩展 (Developer Guide)

如果您希望扩展模型库（例如添加 YOLOv9、RT-DETR 或其他非 YOLO 模型），需要修改核心代码。

### 🔧 如何添加新模型？

**文件位置**: `core/training/trainer.py`

**操作步骤**:
1.  打开 `trainer.py`。
2.  找到 `model_map` 字典（约第 55 行）：
    ```python
    model_map = {
        "YOLOv8-Nano": "yolov8n.pt",
        "YOLOv8-Small": "yolov8s.pt",
        # 在这里添加您的新模型
        "YOLOv8-Large": "yolov8l.pt",
        "YOLOv9-C": "yolov9c.pt"  # 示例
    }
    ```
3.  **修改 UI 选项**:
    *   打开 `ui/wizards/pages/step3_model_params.py`。
    *   找到 `self.combo_model.addItems([...])`，将您的新模型名称加入列表中。

### 🛠️ 如何集成非 YOLO 模型（如 TensorFlow/Paddle）？

目前的 `TrainingWorker` 深度绑定了 `ultralytics` 库。如果您需要支持完全不同的框架：
1.  **定义新 Worker**: 复制 `TrainingWorker` 类，重命名为 `CustomTrainingWorker`。
2.  **重写 `run` 方法**: 在 `run` 方法中替换为您自己的训练代码（调用 TF 或 Paddle 的 API）。
3.  **UI 路由**: 在 `Step4Training` 页面中，根据用户选择的任务类型，实例化对应的 Worker（YOLO Worker 或 Custom Worker）。

---

## 4. 训练产物与结果

所有训练结果（日志、权重、图表）都会保存在 `runs/` 目录下：
*   `runs/detect/trainX/`：目标检测任务结果。
*   `runs/segment/trainX/`：图像分割任务结果。
*   `weights/best.pt`：该次训练的最佳权重，**这是您后续用于推理或导出的核心文件**。

---

如有更多疑问，欢迎查阅代码注释或联系开发团队。
