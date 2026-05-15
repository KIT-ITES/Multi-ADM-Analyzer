import json
from pathlib import Path
from typing import Any


class JsonWriter:
    """handles debug/stat output"""

    def write(self, data: Any, output_dir: str | Path, file_name: str) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        path = output_dir / f"log_{file_name}"

        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file)
            file.write("\n")

        return path