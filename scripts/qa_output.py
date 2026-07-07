from __future__ import annotations

import argparse

from court_ocr_extract.qa import print_safe_qa, qa_excel


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--excel", required=True)
    args = parser.parse_args()
    print_safe_qa(qa_excel(args.excel))


if __name__ == "__main__":
    main()
