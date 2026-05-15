from typing import Mapping

from multi_adm_analyzer.config.settings import Settings
from multi_adm_analyzer.domain.overlay_mode import OverlayMode
from multi_adm_analyzer.pipelines.base_overlay_pipeline import BaseOverlayPipeline
from multi_adm_analyzer.stats.common import build_absolute_counts


class OverlayPipeline(BaseOverlayPipeline):
    def __init__(self, settings: Settings, mode: OverlayMode = OverlayMode.INTERSECTION):
        super().__init__(settings, mode)

    @property
    def pipeline_label(self) -> str:
        return "Overlay pipeline"

    @property
    def enable_single_run_highlighting(self) -> bool:
        return True

    @property
    def output_subtitle_prefix(self) -> str:
        return (
            f"{self.settings.threshold}_"
            if self.settings.threshold != 0.0
            else ""
        )

    def _build_presence_maps(self, scenario_name: str, grid, values_by_adm: Mapping[str, dict[int, list[float]]],) -> dict[str, dict[int, int]]:
        return {
            adm_name: build_absolute_counts(values) for adm_name, values in values_by_adm.items()
        }

    def _write_debug_values(self, scenario_name: str, values_by_adm: Mapping[str, dict[int, list[float]]],
                            presence_by_adm: Mapping[str, Mapping[int, object]],
                            flags_by_cell: dict[int, int]) -> None:
        for adm_name, values in values_by_adm.items():
            self.json_writer.write(data = values,
                                   output_dir = self.output_dir,
                                   file_name = f"{adm_name}.txt_{scenario_name}")

        self.json_writer.write(data=flags_by_cell,
                               output_dir=self.output_dir,
            file_name=(f"{self.settings.adm1}-"
                       f"{self.settings.adm2}-"
                       f"{self.settings.adm3}.txt_{scenario_name}"
                       ),
                               )