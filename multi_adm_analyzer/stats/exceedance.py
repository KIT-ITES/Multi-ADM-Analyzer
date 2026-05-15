from dataclasses import dataclass
from typing import Mapping

import numpy as np


@dataclass(frozen = True, slots = True)
class ExceedanceSummary:
    min_value: float | None
    max_value: float | None
    mean_value: float | None
    median_value: float | None
    cells_above_zero: int
    cells_equal_zero: int
    cells_nan: int
    total_cells: int

    def to_lines(self, title: str = "Exceedance probability statistics") -> list[str]:
        lines = [f"\n\n----====== {title} =====----"]

        if self.min_value is not None:
            lines.append(f"  Min: {self.min_value:.4f}")
            lines.append(f"  Max: {self.max_value:.4f}")
            lines.append(f"  Mean: {self.mean_value:.4f}")
            lines.append(f"  Median: {self.median_value:.4f}")

        lines.append(f"  Cells with prob > 0: {self.cells_above_zero} / {self.total_cells}")
        lines.append(f"  Cells with prob = 0: {self.cells_equal_zero}")
        lines.append(f"  Cells with NaN: {self.cells_nan}")

        return lines


@dataclass(frozen = True, slots = True)
class ExceedanceResult:
    probabilities_by_cell: dict[int, float]
    summary: ExceedanceSummary


class ExceedanceCalculator:
    def __init__(self, exceed_level: float, threshold: float = 0.0):
        self.exceed_level = float(exceed_level)
        self.threshold = float(threshold)

    def compute(self, values_by_cell: Mapping[int, list[float]], cell_ids: list[int] | None = None,) -> ExceedanceResult:
        if cell_ids is None:
            cell_ids = sorted(int(cell) for cell in values_by_cell.keys())

        probabilities_by_cell: dict[int, float] = {}
        all_probabilities: list[float] = []

        for cell_id in cell_ids:
            values = values_by_cell.get(cell_id)

            if not values:
                probability = float("nan")
            else:
                arr = np.asarray(values, dtype = np.float32)
                probability = float(np.mean(arr >= self.exceed_level))

            all_probabilities.append(probability)

            if not np.isnan(probability) and probability > self.threshold:
                probabilities_by_cell[cell_id] = probability

        summary = self._summarize(all_probabilities)

        return ExceedanceResult(probabilities_by_cell = probabilities_by_cell,
                                summary = summary)

    @staticmethod
    def _summarize(probabilities: list[float]) -> ExceedanceSummary:
        arr = np.asarray(probabilities, dtype=np.float32)

        valid = arr[~np.isnan(arr)]
        positive = valid[valid > 0]

        if positive.size == 0:
            return ExceedanceSummary(min_value = None,
                                     max_value = None,
                                     mean_value = None,
                                     median_value = None,
                                     cells_above_zero = 0,
                                     cells_equal_zero = int(np.sum(valid == 0)),
                                     cells_nan = int(np.sum(np.isnan(arr))),
                                     total_cells = int(arr.size)
                                     )

        return ExceedanceSummary(min_value = float(np.min(positive)),
                                 max_value = float(np.max(positive)),
                                 mean_value = float(np.mean(positive)),
                                 median_value = float(np.median(positive)),
                                 cells_above_zero = int(positive.size),
                                 cells_equal_zero = int(np.sum(valid == 0)),
                                 cells_nan = int(np.sum(np.isnan(arr))),
                                 total_cells = int(arr.size)
                                 )