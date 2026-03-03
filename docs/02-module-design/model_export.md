# 模型导出模块设计 (Model Export)

## 1. 功能概述
本模块负责将训练好的 PyTorch 模型 (`.pt`) 转换为工业级部署格式（ONNX / TensorRT），并提供简单的 Python/C++ 推理 Demo 代码生成功能，闭环“训练-部署”流程。

## 2. ✅ 优先级
**中 (Medium)** - 在训练功能稳定后开发。

## 3. ⚠️ 潜在风险
- **算子支持度**：部分自定义 PyTorch 算子（如 Deformable Conv）在导出 ONNX 时可能失败，需提供 fallback 方案或明确不支持列表。
- **环境依赖**：ONNX Runtime GPU 版本与 CUDA 版本的对应关系极其严格，需在文档中明确兼容性矩阵。

## 4. 🔍 确认点 (Checkpoints)
- [ ] **导出格式范围**：
    - 必须支持：ONNX。
    - 是否支持：TensorRT Engine (仅限本机部署), TorchScript (服务端部署)？
- [ ] **动态尺寸支持**：
    - 导出时是否强制固定 Input Shape (如 640x640)？（固定尺寸推理速度更快，但灵活性差）
- [ ] **量化支持 (Quantization)**：
    - 是否提供 FP16 / INT8 量化选项？（显著降低模型体积，但可能损失精度）
- [ ] **打包交付物**：
    - 导出时是否自动生成一个 `inference.py` 脚本，方便用户直接调用？
