import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping

import numpy as np


ComparisonDomain = Literal[
    "union_nonzero",
    "intersection_nonzero",
    "all",
]


@dataclass(frozen = True, slots = True)
class InterModelMetrics:
    scenario_name: str
    first_model: str
    second_model: str
    comparison_domain: str
    n_cells: int

    mean_first: float
    mean_second: float

    mean_bias: float
    rmse: float
    pattern_correlation: float
    fractional_bias: float

    def to_lines(self) -> list[str]:
        return [
            "",
            f"----====== Inter-model metrics: {self.scenario_name} =====----",
            f"Pair: {self.first_model} - {self.second_model}",
            f"Comparison domain: {self.comparison_domain}",
            f"Cells in comparison domain: {self.n_cells}",
            f"Mean {self.first_model}: {self._format(self.mean_first)}",
            f"Mean {self.second_model}: {self._format(self.mean_second)}",
            f"MB ({self.first_model} - {self.second_model}): {self._format(self.mean_bias)}",
            f"RMSE: {self._format(self.rmse)}",
            f"Pattern correlation r: {self._format(self.pattern_correlation)}",
            f"Fractional bias FB: {self._format(self.fractional_bias)}",
        ]

    def to_csv_row(self) -> dict[str, object]:
        return {
            "scenario": self.scenario_name,
            "model_a": self.first_model,
            "model_b": self.second_model,
            "comparison_domain": self.comparison_domain,
            "n_cells": self.n_cells,
            "mean_a": self.mean_first,
            "mean_b": self.mean_second,
            "mb_a_minus_b": self.mean_bias,
            "rmse": self.rmse,
            "pattern_correlation": self.pattern_correlation,
            "fractional_bias_a_minus_b": self.fractional_bias,
        }

    @staticmethod
    def csv_header() -> list[str]:
        return [
            "scenario",
            "model_a",
            "model_b",
            "comparison_domain",
            "n_cells",
            "mean_a",
            "mean_b",
            "mb_a_minus_b",
            "rmse",
            "pattern_correlation",
            "fractional_bias_a_minus_b",
        ]

    @staticmethod
    def _format(value: float) -> str:
        if math.isnan(value):
            return "nan"

        return f"{value:.6f}"


class InterModelMetricsCalculator:
    def __init__(self, comparison_domain: ComparisonDomain = "union_nonzero"):
        self.comparison_domain = comparison_domain

    def compute(self, scenario_name: str, first_model: str, second_model: str,
                first_frequency_by_cell: Mapping[int, float], second_frequency_by_cell: Mapping[int, float]) -> InterModelMetrics:

        cells = self._comparison_cells(first_frequency_by_cell = first_frequency_by_cell,
                                       second_frequency_by_cell = second_frequency_by_cell)

        if not cells:
            return InterModelMetrics(scenario_name = scenario_name,
                                     first_model = first_model,
                                     second_model = second_model,
                                     comparison_domain = self.comparison_domain,
                                     n_cells = 0,
                                     mean_first = float("nan"),
                                     mean_second = float("nan"),
                                     mean_bias = float("nan"),
                                     rmse = float("nan"),
                                     pattern_correlation = float("nan"),
                                     fractional_bias = float("nan"))

        first = np.asarray([first_frequency_by_cell.get(cell, 0.0) for cell in cells], dtype=np.float64)

        second = np.asarray([second_frequency_by_cell.get(cell, 0.0) for cell in cells], dtype=np.float64)

        diff = first - second

        mean_first = float(np.mean(first))
        mean_second = float(np.mean(second))

        mean_bias = float(np.mean(diff))
        rmse = float(np.sqrt(np.mean(diff ** 2)))
        pattern_correlation = self._pattern_correlation(first, second)
        fractional_bias = self._fractional_bias(mean_first, mean_second)

        return InterModelMetrics(scenario_name = scenario_name,
                                 first_model = first_model,
                                 second_model = second_model,
                                 comparison_domain = self.comparison_domain,
                                 n_cells = len(cells),
                                 mean_first = mean_first,
                                 mean_second = mean_second,
                                 mean_bias = mean_bias,
                                 rmse = rmse,
                                 pattern_correlation = pattern_correlation,
                                 fractional_bias = fractional_bias)

    def _comparison_cells(self, first_frequency_by_cell: Mapping[int, float], second_frequency_by_cell: Mapping[int, float]) -> list[int]:

        all_cells = set(first_frequency_by_cell) | set(second_frequency_by_cell)

        if self.comparison_domain == "all":
            return sorted(int(cell) for cell in all_cells)

        if self.comparison_domain == "union_nonzero":
            return sorted(int(cell) for cell in all_cells
                          if ( first_frequency_by_cell.get(cell, 0.0) > 0.0 or second_frequency_by_cell.get(cell, 0.0) > 0.0)
            )

        if self.comparison_domain == "intersection_nonzero":
            return sorted(int(cell) for cell in all_cells
                          if (first_frequency_by_cell.get(cell, 0.0) > 0.0 and second_frequency_by_cell.get(cell, 0.0) > 0.0)
            )

        raise ValueError(f"Unsupported comparison domain: {self.comparison_domain!r}")

    @staticmethod
    def _pattern_correlation(first: np.ndarray, second: np.ndarray) -> float:
        if first.size < 2:
            return float("nan")

        first_anomaly = first - np.mean(first)
        second_anomaly = second - np.mean(second)

        denominator = np.sqrt(np.sum(first_anomaly ** 2)) * np.sqrt(np.sum(second_anomaly ** 2))

        if denominator == 0.0:
            return float("nan")

        return float(np.sum(first_anomaly * second_anomaly) / denominator)

    @staticmethod
    def _fractional_bias(mean_first: float, mean_second: float) -> float:
        denominator = mean_first + mean_second

        if denominator == 0.0:
            return float("nan")

        return float(2.0 * (mean_first - mean_second) / denominator)


class InterModelMetricsWriter:
    def append_text(self, output_path: str | Path, metrics: InterModelMetrics) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("a", encoding="utf-8") as file:
            file.write("\n".join(metrics.to_lines()))
            file.write("\n")

        return output_path

    def append_csv(self, output_path: str | Path, metrics: InterModelMetrics) -> Path:

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        write_header = not output_path.exists() or output_path.stat().st_size == 0

        with output_path.open("a", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file,
                                    fieldnames=InterModelMetrics.csv_header())

            if write_header:
                writer.writeheader()

            writer.writerow(metrics.to_csv_row())

        return output_path