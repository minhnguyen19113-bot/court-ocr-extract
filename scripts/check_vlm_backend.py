from __future__ import annotations

import argparse
import urllib.request

from court_ocr_extract.settings import get_settings
from court_ocr_extract.vlm_backends import get_vlm_backend


def main() -> None:
    parser = argparse.ArgumentParser(description="Check local VLM backend configuration.")
    parser.add_argument("--provider", default=None)
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if the local endpoint is not reachable.")
    args = parser.parse_args()

    settings = get_settings()
    backend = get_vlm_backend(settings, provider=args.provider)
    status = backend.check_available()
    print(f"VLM provider: {backend.provider}")
    print(f"VLM model: {backend.model_name}")
    print(f"Available: {status.available}")
    print(f"Reason: {status.reason}")
    if backend.provider == "ollama":
        reachable = _check_ollama(settings.vlm_base_url)
        print(f"Ollama endpoint reachable: {reachable}")
        if args.strict and not reachable:
            raise SystemExit(1)
    elif args.strict and not status.available:
        raise SystemExit(1)


def _check_ollama(base_url: str) -> bool:
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/api/tags", timeout=2) as response:
            return response.status < 500
    except Exception:
        return False


if __name__ == "__main__":
    main()

