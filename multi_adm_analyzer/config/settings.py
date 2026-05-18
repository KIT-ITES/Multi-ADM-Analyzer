import json
from dataclasses import dataclass
from multiprocessing import cpu_count
from pathlib import Path
from typing import Any

from multi_adm_analyzer.config.path_resolver import PathResolver
from multi_adm_analyzer.domain.models import AdmPaths


@dataclass(frozen = True, slots = True)
class Settings:
    """loads and validates config"""
    raw: dict[str, Any]

    site_name: str
    site_coord: tuple[float, float]

    adm1: str
    adm2: str | None
    adm3: str | None

    epsg: int

    root_1: Path
    root_2: Path | None
    root_3: Path | None

    grid_path: Path
    log_path: Path
    write_debug_logs: bool
    basemap_path: Path | None

    exceed_level: float
    exceed_unit: str
    threshold: float

    year: str
    visual_parameters: dict[str, Any]
    with_local_basemap_overlay: bool
    api_key: str | None
    plot_settings: dict[str, Any]

    n_cpus: int

    @classmethod
    def from_file(cls, config_path: str | Path) -> "Settings":
        config_path = Path(config_path)

        with config_path.open("r", encoding="utf-8") as file:
            raw = json.load(file)

        site_name = raw["site_name"]
        resolver = PathResolver(site_name)

        adm1 = raw["ADM1"]
        adm2 = raw.get("ADM2")
        adm3 = raw.get("ADM3")

        site_coord = cls._parse_site_coord(raw["site_coord"])

        root_1 = resolver.resolve_adm_path(raw["root_1"], adm1)
        root_2 = resolver.resolve_adm_path(raw["root_2"], adm2) if adm2 and "root_2" in raw else None
        root_3 = resolver.resolve_adm_path(raw["root_3"], adm3) if adm3 and "root_3" in raw else None

        grid_path = resolver.resolve_named_path(raw["grid_path"], {})
        log_path = resolver.resolve_named_path(raw["log_path"], {})
        write_debug_logs = bool(raw.get("write_debug_logs", True))

        basemap_path = Path(raw["basemap_path"]) if raw.get("basemap_path") else None

        api_key = cls._load_api_key(raw.get("api_key_file"))

        return cls(
            raw = raw,
            site_name = site_name,
            site_coord = site_coord,
            epsg = int(raw.get("epsg", 3857)),
            adm1 = adm1,
            adm2 = adm2,
            adm3 = adm3,
            root_1 = root_1,
            root_2 = root_2,
            root_3 = root_3,
            grid_path = grid_path,
            log_path = log_path,
            write_debug_logs = write_debug_logs,
            basemap_path = basemap_path,
            exceed_level = float(raw["exceed_level"]),
            exceed_unit = str(raw["exceed_unit"]),
            threshold = float(raw["threshold"]),
            year = str(raw["year"]),
            visual_parameters = raw["visual_parameters"],
            with_local_basemap_overlay = bool(raw["with_local_basemap_overlay"]),
            api_key = api_key,
            plot_settings = raw.get("plot_settings", {}),
            n_cpus = cpu_count(),
        )

    @staticmethod
    def _parse_site_coord(value: str) -> tuple[float, float]:
        parts = value.replace(" ", "").split(",")

        if len(parts) != 2:
            raise ValueError(f"Invalid site_coord format: {value!r}")

        lon, lat = parts
        return float(lon), float(lat)

    def adm_paths_1(self) -> AdmPaths:
        return AdmPaths(self.adm1, self.root_1)

    def adm_paths_2(self) -> AdmPaths:
        if self.adm2 is None or self.root_2 is None:
            raise ValueError("ADM2/root_2 is not configured")

        return AdmPaths(self.adm2, self.root_2)

    def adm_paths_3(self) -> AdmPaths:
        if self.adm3 is None or self.root_3 is None:
            raise ValueError("ADM3/root_3 is not configured")

        return AdmPaths(self.adm3, self.root_3)

    def probabilistic_output_dir(self) -> Path:
        return self.root_1.parent / f"{self.year}_Plots_Data_probabilistic_maps"

    def relative_output_dir(self) -> Path:
        if self.adm2 is None:
            raise ValueError("ADM2 is required for relative-frequency output")

        template = self.raw["relative_adms"]
        resolver = PathResolver(self.site_name)

        return resolver.resolve_named_path(
            template,
            {
                "ADM1": self.adm1,
                "ADM2": self.adm2,
            },
        )

    def overlay_output_dir(self) -> Path:
        if self.adm2 is None or self.adm3 is None:
            raise ValueError("ADM2 and ADM3 are required for overlay output")

        template = self.raw["overlay_adms"]
        resolver = PathResolver(self.site_name)

        return resolver.resolve_named_path(
            template,
            {
                "ADM1": self.adm1,
                "ADM2": self.adm2,
                "ADM3": self.adm3,
            },
        )

    @staticmethod
    def _load_api_key(path: str | Path | None) -> str | None:
        if path is None:
            return None

        key_path = Path(path)

        if not key_path.exists():
            raise FileNotFoundError(f"API key file does not exist: {key_path}")

        key = key_path.read_text(encoding = "utf-8").strip()

        if not key:
            raise ValueError(f"API key file is empty: {key_path}")

        return key