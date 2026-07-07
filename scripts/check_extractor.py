from __future__ import annotations

import argparse

from court_ocr_extract.extractors import get_extractor_backend


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", required=True)
    args = parser.parse_args()
    extractor = get_extractor_backend(args.backend)
    status = extractor.check_available()
    print(f"Extractor backend: {status.name}")
    print(f"Available: {status.available}")
    print(f"Reason: {status.reason}")
    if not status.available:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
