from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from court_ocr_extract.config import get_settings
from court_ocr_extract.ocr_surya import load_ocr_document


def main() -> None:
    parser = argparse.ArgumentParser(description="Tạo dataset ocr_raw -> ocr_corrected dạng JSONL.")
    parser.add_argument("--raw-dir", type=Path, default=None)
    parser.add_argument("--corrected-dir", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    settings = get_settings()
    raw_dir = args.raw_dir or settings.ocr_raw_dir
    corrected_dir = args.corrected_dir or settings.ocr_corrected_dir
    output = args.output or (settings.annotations_dir / "surya_correction_dataset.jsonl")
    output.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with output.open("w", encoding="utf-8") as file_handle:
        for raw_json in sorted(raw_dir.glob("*.json")):
            document = load_ocr_document(raw_json)
            corrected_path = _find_corrected_text(corrected_dir, raw_json.stem)
            record = {
                "id": raw_json.stem,
                "source_file": document.source_file,
                "ocr_raw": document.text,
                "ocr_corrected": corrected_path.read_text(encoding="utf-8") if corrected_path else "",
            }
            file_handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1

    print(json.dumps({"output": str(output), "records": count}, ensure_ascii=False, indent=2))


def _find_corrected_text(corrected_dir: Path, stem: str) -> Path | None:
    for candidate in [
        corrected_dir / f"{stem}_corrected.txt",
        corrected_dir / f"{stem}.txt",
        corrected_dir / f"{stem}_normalized.txt",
    ]:
        if candidate.exists():
            return candidate
    return None


if __name__ == "__main__":
    main()
