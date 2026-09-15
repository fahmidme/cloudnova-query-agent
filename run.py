"""One reviewer command: isolated Python setup followed by the guided journey."""

import os
from pathlib import Path
import subprocess
import sys

import bootstrap


def main() -> int:
    root = Path(__file__).resolve().parent
    print("Preparing the local Python environment...", flush=True)
    python = bootstrap.ensure_environment()
    return subprocess.call([str(python), "-m", "app.guided"], cwd=root)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nSession ended.")
        sys.exit(130)
    except OSError as exc:
        print(f"Setup could not complete: {exc}", file=sys.stderr)
        sys.exit(2)
