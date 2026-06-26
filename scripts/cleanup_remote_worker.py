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
from court_ocr_extract.remote_worker.client import RemoteWorkerClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the remote GPU worker to delete temporary files.")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--token", default=None)
    args = parser.parse_args()

    settings = get_settings()
    client = RemoteWorkerClient(
        base_url=args.base_url or settings.gpu_worker_base_url,
        token=args.token if args.token is not None else settings.gpu_worker_token,
        timeout=settings.gpu_worker_timeout_seconds,
        retries=settings.gpu_worker_retries,
    )
    print(json.dumps(client.cleanup(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
