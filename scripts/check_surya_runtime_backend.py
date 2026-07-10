from __future__ import annotations

import argparse
import json

from court_ocr_extract.ocr_backends.surya_runtime import collect_surya_runtime_diagnostics


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-gpu-container", action="store_true")
    args = parser.parse_args(argv)
    diagnostics = collect_surya_runtime_diagnostics(check_gpu_container=args.check_gpu_container)
    print(json.dumps(diagnostics, ensure_ascii=False, indent=2))
    if not diagnostics["docker"]["available"]:
        raise SystemExit(1)
    if args.check_gpu_container and not diagnostics["gpu_container"].get("ok"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
