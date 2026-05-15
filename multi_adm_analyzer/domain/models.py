from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen = True, slots = True)
class AdmPaths:
    adm_name: str
    root: Path


@dataclass(frozen = True, slots = True)
class Scenario:
    name: str
    paths_by_adm: Mapping[str, Path]


@dataclass(frozen = True, slots = True)
class CellExtrema:
    min_cell: int
    min_value: float
    max_cell: int
    max_value: float