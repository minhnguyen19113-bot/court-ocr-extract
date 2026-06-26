from __future__ import annotations


def recommended_local_model_config(model_size: str = "7b") -> dict[str, str | int | float]:
    if model_size.lower() in {"14b", "qwen14b"}:
        return {
            "model": "Qwen/Qwen2.5-14B-Instruct-AWQ",
            "gpu_memory_utilization": 0.90,
            "max_model_len": 8192,
            "notes": "Dùng khi RTX 4090/3090 24GB còn đủ VRAM sau OCR hoặc chạy LLM riêng.",
        }
    return {
        "model": "Qwen/Qwen2.5-7B-Instruct-AWQ",
        "gpu_memory_utilization": 0.82,
        "max_model_len": 8192,
        "notes": "Mặc định tiết kiệm cho RTX 3090/3090 Ti/4090 24GB.",
    }
