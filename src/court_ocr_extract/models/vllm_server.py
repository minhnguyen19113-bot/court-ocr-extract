from __future__ import annotations


def build_vllm_command(
    model: str,
    *,
    host: str = "0.0.0.0",
    port: int = 8001,
    gpu_memory_utilization: float = 0.82,
    max_model_len: int = 8192,
) -> list[str]:
    return [
        "python",
        "-m",
        "vllm.entrypoints.openai.api_server",
        "--host",
        host,
        "--port",
        str(port),
        "--model",
        model,
        "--gpu-memory-utilization",
        str(gpu_memory_utilization),
        "--max-model-len",
        str(max_model_len),
    ]
