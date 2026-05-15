import gc
from typing import Mapping

import numpy as np
from geopandas import GeoDataFrame


class GridJoiner:
    """attaches computed cell values"""

    DEFAULT_VALUE_COLUMN = "grid_class"

    def attach_values(self, grid: GeoDataFrame, values_by_cell: Mapping[int, float],
                      value_column: str = DEFAULT_VALUE_COLUMN,) -> GeoDataFrame:
        result = grid.copy(deep = True)
        cell_column = self._detect_cell_column(result)

        result[value_column] = result[cell_column].astype(int).map(values_by_cell)
        result = result[result.geometry.notnull()]

        gc.collect()
        return result

    def extrema(self, grid: GeoDataFrame, value_column: str = DEFAULT_VALUE_COLUMN,) -> tuple[int, float, int, float]:
        cell_column = self._detect_cell_column(grid)

        values = dict(zip(grid[cell_column].astype(int), grid[value_column]))

        clean_values = {
            int(cell): float(value)
            for cell, value in values.items()
            if value is not None and not np.isnan(value)
        }

        if not clean_values:
            raise ValueError(f"No valid values found in column {value_column!r}")

        min_cell = min(clean_values, key = clean_values.get)
        max_cell = max(clean_values, key = clean_values.get)

        return min_cell, clean_values[min_cell], max_cell, clean_values[max_cell]

    @staticmethod
    def _detect_cell_column(grid: GeoDataFrame) -> str:
        if "Cell" in grid.columns:
            return "Cell"

        if "cell_id" in grid.columns:
            return "cell_id"

        raise ValueError("Grid must contain either 'Cell' or 'cell_id'")