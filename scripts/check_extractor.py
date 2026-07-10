from __future__ import annotations

import argparse

from court_ocr_extract.extractors import get_extractor_backend


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Static extractor configuration check; no model endpoint is contacted."
    )
    parser.add_argument("--backend", default="local_llm")
    args = parser.parse_args(argv)
    extractor = get_extractor_backend(args.backend)
    status = extractor.check_available()
    print("Check mode: static configuration only (no endpoint request)")
    print(f"Extractor backend: {status.name}")
    print(f"Available: {status.available}")
    print(f"Reason: {status.reason}")
    return 0 if status.available else 1


if __name__ == "__main__":
    raise SystemExit(main())
