from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots = True)
class PlotContext:
    save_dir: Path
    site_name: str
    site_coord: tuple[float, float]
    epsg: int

    api_key: str | None

    visual_parameters: dict[str, Any]
    with_local_basemap_overlay: bool
    basemap_path: Path | None

    figure_size: tuple[float, float] = (12.0, 10.0)
    dpi: int = 600

    font_size_title: int = 14
    font_size_axis_label: int = 12
    font_size_tick_label: int = 11
    font_size_ring_label: int = 10
    font_size_bearing_label: int = 10
    font_size_legend: int = 10
    font_size_legend_title: int = 11

    show_legend: bool = True
    export_legend: bool = False
    legend_frame: bool = True

    basemap_provider: str = "positron"

    @classmethod
    def from_settings(cls, settings):
        plot_settings = settings.plot_settings

        return cls(
            save_dir = Path("."),
            site_name = settings.site_name,
            site_coord = settings.site_coord,

            epsg = settings.epsg,
            api_key = settings.api_key,

            visual_parameters = settings.visual_parameters,
            with_local_basemap_overlay = settings.with_local_basemap_overlay,
            basemap_path = settings.basemap_path,

            figure_size = tuple(plot_settings.get("figure_size", [12.0, 10.0])),
            dpi = int(plot_settings.get("dpi", 600)),

            font_size_title = int(plot_settings.get("font_size_title", 14)),
            font_size_axis_label = int(plot_settings.get("font_size_axis_label", 12)),
            font_size_tick_label = int(plot_settings.get("font_size_tick_label", 11)),
            font_size_ring_label = int(plot_settings.get("font_size_ring_label", 10)),
            font_size_bearing_label = int(plot_settings.get("font_size_bearing_label", 10)),
            font_size_legend = int(plot_settings.get("font_size_legend", 10)),
            font_size_legend_title = int(plot_settings.get("font_size_legend_title", 11)),

            show_legend = bool(plot_settings.get("show_legend", True)),
            export_legend = bool(plot_settings.get("export_legend", False)),
            legend_frame = bool(plot_settings.get("legend_frame", True)),

            basemap_provider = str(plot_settings.get("basemap_provider", "positron")),
        )