from pathlib import Path
from typing import Iterable


class StatisticsWriter:
    def append_lines(self, output_path: str | Path, lines: Iterable[str]) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents = True, exist_ok = True)

        with output_path.open("a", encoding="utf-8") as file:
            file.write("\n".join(lines))
            file.write("\n")

        return output_path