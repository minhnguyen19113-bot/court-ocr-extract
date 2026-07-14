from __future__ import annotations


def recommended_local_model_config(model_size: str = "3b") -> dict[str, str | int | float]:
    if model_size.lower() in {"14b", "qwen14b"}:
        return {
            "model": "Qwen/Qwen2.5-14B-Instruct-AWQ",
            "gpu_memory_utilization": 0.90,
            "max_model_len": 8192,
            "notes": "Dùng khi RTX 4090/3090 24GB còn đủ VRAM sau OCR hoặc chạy LLM riêng.",
        }
    if model_size.lower() in {"7b", "qwen7b"}:
        return {
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "gpu_memory_utilization": 0.90,
            "max_model_len": 8192,
            "notes": "Không dùng mặc định trên RTX 5060 Ti 16GB; cần runtime profile khác.",
        }
    return {
        "model": "Qwen/Qwen2.5-3B-Instruct",
        "gpu_memory_utilization": 0.88,
        "max_model_len": 8192,
        "notes": "Mặc định đã xác nhận cho RTX 5060 Ti 16GB.",
    }
