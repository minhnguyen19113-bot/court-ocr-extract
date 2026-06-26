from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Mermaid workflow to PNG/SVG using mermaid-cli.")
    parser.add_argument("--input", type=Path, default=Path("docs/workflow.mmd"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/workflow"))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for suffix in ["png", "svg"]:
        output = args.output_dir / f"workflow.{suffix}"
        subprocess.run(
            ["npx", "@mermaid-js/mermaid-cli", "-i", str(args.input), "-o", str(output)],
            check=True,
        )
        print(output)


if __name__ == "__main__":
    main()
