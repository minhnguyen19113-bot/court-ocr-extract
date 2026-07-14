from __future__ import annotations

import json

from court_ocr_extract.local_llm.preflight import check_llm_backend
from court_ocr_extract.settings import get_settings


def main() -> int:
    result = check_llm_backend(get_settings())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
