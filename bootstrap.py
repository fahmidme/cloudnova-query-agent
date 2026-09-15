"""Create an isolated, dependency-free environment without changing host Python."""

import os
from pathlib import Path
import sys
import venv


def main():
    if sys.version_info < (3, 11):
        raise SystemExit("Python 3.11+ is required.")
    try:
        import sqlite3
        with sqlite3.connect(":memory:") as conn:
            conn.execute("SELECT 1")
    except ImportError:
        raise SystemExit("This Python installation needs sqlite3 support.") from None
    root = Path(__file__).resolve().parent
    # No packages are needed, so pip/ensurepip downloads are unnecessary.
    venv.EnvBuilder(with_pip=False).create(root / ".venv")
    executable = ".venv\\Scripts\\python.exe" if os.name == "nt" else ".venv/bin/python"
    print(f"Environment ready. From {root.name}, run:")
    print(f"  {executable} -m app demo")
    print(f"  {executable} -m unittest discover -s tests -v")


if __name__ == "__main__":
    main()
