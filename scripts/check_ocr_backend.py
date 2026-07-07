from __future__ import annotations

import argparse

from court_ocr_extract.ocr_backends import get_ocr_backend


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", required=True)
    args = parser.parse_args()
    backend = get_ocr_backend(args.backend)
    status = backend.check_available()
    print(f"OCR backend: {status.name}")
    print(f"Available: {status.available}")
    print(f"Reason: {status.reason}")
    if not status.available:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
