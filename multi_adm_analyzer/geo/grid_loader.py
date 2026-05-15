from pathlib import Path

import geopandas as gpd
from geopandas import GeoDataFrame


class GridLoader:
    """reads shapefile/grid"""
    def load(self, path: str | Path) -> GeoDataFrame:
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Grid file does not exist: {path}")

        grid = gpd.read_file(path)

        if "geometry" not in grid.columns:
            raise ValueError(f"Grid has no geometry column: {path}")

        if grid.crs is None:
            raise ValueError(f"Grid CRS is missing: {path}")

        return grid