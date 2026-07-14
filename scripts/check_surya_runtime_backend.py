from __future__ import annotations

import argparse
import json

from court_ocr_extract.ocr_backends.surya_runtime import collect_surya_runtime_diagnostics


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-gpu-container", action="store_true")
    parser.add_argument("--surya-docker-binary", default=None)
    parser.add_argument("--gpu-container-timeout-seconds", type=int, default=180)
    parser.add_argument("--gpu-test-image", default="nvidia/cuda:12.4.1-base-ubuntu22.04")
    args = parser.parse_args(argv)
    diagnostics = collect_surya_runtime_diagnostics(
        check_gpu_container=args.check_gpu_container,
        docker_binary=args.surya_docker_binary,
        gpu_container_timeout_seconds=args.gpu_container_timeout_seconds,
        gpu_test_image=args.gpu_test_image,
    )
    print(json.dumps(diagnostics, ensure_ascii=False, indent=2))
    if not diagnostics["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
