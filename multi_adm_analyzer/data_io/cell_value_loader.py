from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path
from typing import DefaultDict

from multi_adm_analyzer.data_io.binary_reader import BinaryGridReader

CellValues = dict[int, list[float]]


def _read_file_worker(path: str) -> dict[int, float]:
    reader = BinaryGridReader()
    last_column = reader.read_last_column(path)
    return {cell_id: float(value) for cell_id, value in enumerate(last_column)}


class CellValueLoader:
    def __init__(self, workers: int, chunk_size: int = 2):
        self.workers = max(1, workers)
        self.chunk_size = chunk_size

    def load_folder(self, folder: str | Path) -> CellValues:
        folder = Path(folder)
        files = [path for path in folder.iterdir() if path.is_file()]

        if not files:
            return {}

        worker_count = min(self.workers, len(files))
        values_by_cell: DefaultDict[int, list[float]] = defaultdict(list)

        with Pool(worker_count) as pool:
            results = pool.imap_unordered(_read_file_worker, map(str, files), chunksize = self.chunk_size,)

            for file_values in results:
                for cell_id, value in file_values.items():
                    values_by_cell[cell_id].append(value)

        return dict(values_by_cell)