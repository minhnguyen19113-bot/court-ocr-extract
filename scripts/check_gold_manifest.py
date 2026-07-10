from __future__ import annotations

import argparse

from court_ocr_extract.evaluation.manifest import (
    ManifestValidationError,
    load_gold_manifest,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a redacted gold JSONL manifest without reading PDFs or outputs."
    )
    parser.add_argument("--gold", required=True)
    args = parser.parse_args(argv)
    try:
        records = load_gold_manifest(args.gold)
    except ManifestValidationError as exc:
        print(f"Gold manifest: FAIL ({exc})")
        return 1
    print("Gold manifest: PASS")
    print(f"Records validated: {len(records)}")
    print("PII check: no obvious ID/phone/email pattern detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
