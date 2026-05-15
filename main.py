import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
VENV = PROJECT_ROOT / ".venv"

for key in ("PROJ_LIB", "PROJ_DATA", "GDAL_DATA"):
    os.environ.pop(key, None)

os.environ["PATH"] = (
    str(VENV / "Scripts")
    + os.pathsep
    + os.environ.get("PATH", "")
)

from multi_adm_analyzer.cli import main


if __name__ == "__main__":
    main()