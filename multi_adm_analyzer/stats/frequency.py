from dataclasses import dataclass
from typing import Mapping

import numpy as np


@dataclass(frozen = True, slots = True)
class RelativeFrequencyResult:

    first_frequency_by_cell: dict[int, float]
    second_frequency_by_cell: dict[int, float]
    difference_by_cell: dict[int, float]
    absolute_difference_by_cell: dict[int, float]


class RelativeFrequencyCalculator:
    def __init__(self, event_threshold: float = 0.0, include_equal: bool = False):
        self.event_threshold = float(event_threshold)
        self.include_equal = include_equal

    def compute(self, first_values_by_cell: Mapping[int, list[float]], second_values_by_cell: Mapping[int, list[float]], total_files: int,) -> RelativeFrequencyResult:
        if total_files <= 0:
            raise ValueError("total_files must be greater than zero")

        all_cells = set(first_values_by_cell) | set(second_values_by_cell)

        first_frequency_by_cell: dict[int, float] = {}
        second_frequency_by_cell: dict[int, float] = {}
        difference_by_cell: dict[int, float] = {}
        absolute_difference_by_cell: dict[int, float] = {}

        for cell in all_cells:
            first_count = self._event_count(first_values_by_cell.get(cell, []))
            second_count = self._event_count(second_values_by_cell.get(cell, []))

            first_frequency = first_count / total_files
            second_frequency = second_count / total_files

            if first_frequency > 0.0:
                first_frequency_by_cell[int(cell)] = float(first_frequency)

            if second_frequency > 0.0:
                second_frequency_by_cell[int(cell)] = float(second_frequency)

            if first_count == 0 and second_count == 0:
                continue

            difference = first_frequency - second_frequency

            difference_by_cell[int(cell)] = float(difference)
            absolute_difference_by_cell[int(cell)] = float(abs(difference))

        return RelativeFrequencyResult(first_frequency_by_cell = first_frequency_by_cell,
                                       second_frequency_by_cell = second_frequency_by_cell,
                                       difference_by_cell = difference_by_cell,
                                       absolute_difference_by_cell = absolute_difference_by_cell,
        )

    def _event_count(self, values: list[float]) -> int:
        if not values:
            return 0

        arr = np.asarray(values, dtype=np.float32)

        if self.include_equal:
            return int(np.sum(arr >= self.event_threshold))

        return int(np.sum(arr > self.event_threshold))