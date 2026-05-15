import struct
from pathlib import Path

import numpy as np

class BinaryGridReader:
    HEADER_SIZE_BYTES = 8
    DTYPE = ">f4"

    def read_last_column(self, path: str | Path) -> np.ndarray:
        path = Path(path)

        with path.open("rb") as file:
            header = file.read(self.HEADER_SIZE_BYTES)

            if len(header) < self.HEADER_SIZE_BYTES:
                raise ValueError(f"File is too short: {path}")

            rows, cols = struct.unpack(">ii", header)
            expected_count = rows * cols

            data = np.fromfile(file, dtype = self.DTYPE, count = expected_count)

        if data.size != expected_count:
            raise ValueError(f"Invalid binary size in {path}: expected {expected_count} floats, got {data.size}")

        matrix = data.reshape(rows, cols)
        return matrix[:, -1].astype(np.float32)