from __future__ import annotations

from pathlib import Path
from typing import Any

from court_ocr_extract.file_utils import write_json
from court_ocr_extract.models import model_to_dict


def write_result_json(payload: Any, output_path: str | Path) -> Path:
    return write_json(Path(output_path), model_to_dict(payload) if not isinstance(payload, dict) else payload)
