from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from court_ocr_extract.ocr_backends import get_ocr_backend


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", required=True)
    args = parser.parse_args()
    try:
        backend = get_ocr_backend(args.backend)
    except ModuleNotFoundError as exc:
        print(f"OCR backend: {args.backend}")
        print("Available: False")
        print(
            "Reason: Missing runtime dependency while importing backend: "
            f"{exc.name}. Run inside the project virtualenv or install project dependencies."
        )
        raise SystemExit(1)

    status = backend.check_available()
    print(f"OCR backend: {status.name}")
    print(f"Available: {status.available}")
    print(f"Reason: {status.reason}")
    if not status.available:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
