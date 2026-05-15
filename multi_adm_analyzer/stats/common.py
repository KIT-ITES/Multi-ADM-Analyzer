from typing import Mapping

import numpy as np

def build_absolute_counts(values_by_cell: Mapping[int, list[float]]) -> dict[int, int]:
    counts: dict[int, int] = {}

    for cell, values in values_by_cell.items():
        arr = np.asarray(values)
        count = int(np.count_nonzero(arr))

        if count > 0:
            counts[int(cell)] = count

    return counts


def map_single_nonzero_run(values_by_cell: Mapping[int, list[float]]) -> dict[int, int]:
    result: dict[int, int] = {}

    for cell, values in values_by_cell.items():
        arr = np.asarray(values)
        count = int(np.count_nonzero(arr))

        if count == 1:
            index = int(np.nonzero(arr)[0][0])
            result[int(cell)] = index + 1

    return result