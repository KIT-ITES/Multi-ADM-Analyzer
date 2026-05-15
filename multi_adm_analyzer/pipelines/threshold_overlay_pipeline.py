from typing import Mapping

from multi_adm_analyzer.config.settings import Settings
from multi_adm_analyzer.domain.overlay_mode import OverlayMode
from multi_adm_analyzer.pipelines.base_overlay_pipeline import BaseOverlayPipeline
from multi_adm_analyzer.stats.exceedance import ExceedanceCalculator
from multi_adm_analyzer.stats.statistics_writer import StatisticsWriter


class ThresholdOverlayPipeline(BaseOverlayPipeline):
    def __init__(self, settings: Settings, mode: OverlayMode = OverlayMode.INTERSECTION):
        super().__init__(settings, mode)

        self.exceedance_calculator = ExceedanceCalculator(
            exceed_level = settings.exceed_level,
            threshold = settings.threshold,
        )
        self.statistics_writer = StatisticsWriter()

    @property
    def pipeline_label(self) -> str:
        return "Threshold-overlay pipeline"

    @property
    def output_subtitle_prefix(self) -> str:
        return f"{self.settings.threshold}_"

    def _build_presence_maps(self, scenario_name: str, grid, values_by_adm: Mapping[str, dict[int, list[float]]]) -> dict[str, dict[int, float]]:
        cell_column = "Cell" if "Cell" in grid.columns else "cell_id"
        cell_ids = [int(cell) for cell in grid[cell_column]]

        probabilities_by_adm: dict[str, dict[int, float]] = {}

        for adm_name, values_by_cell in values_by_adm.items():
            print(f"\nComputing exceedance probabilities for {adm_name}; "
                  f"exceed_level = {self.settings.exceed_level}, "
                  f"threshold = {self.settings.threshold}")

            result = self.exceedance_calculator.compute(values_by_cell = values_by_cell, cell_ids = cell_ids)

            summary_lines = result.summary.to_lines(title = (f"{adm_name} exceedance probability statistics "
                                                             f"excluding 0 and NaN"))
            print("\n".join(summary_lines))

            if self.settings.write_debug_logs:
                statistics_path = (self.output_dir / f"{scenario_name}_threshold_overlay_statistical_data_{adm_name}.txt")

                self.statistics_writer.append_lines(output_path = statistics_path,
                                                    lines = summary_lines)

            probabilities_by_adm[adm_name] = result.probabilities_by_cell

        return probabilities_by_adm

    def _write_debug_values(self, scenario_name: str, values_by_adm: Mapping[str, dict[int, list[float]]],
                            presence_by_adm: Mapping[str, Mapping[int, object]],
                            flags_by_cell: dict[int, int]) -> None:
        for adm_name, probabilities in presence_by_adm.items():
            self.json_writer.write(
                data = probabilities,
                output_dir = self.output_dir,
                file_name = f"probabilities_{adm_name}.txt_{scenario_name}",
            )

        self.json_writer.write(
            data = flags_by_cell,
            output_dir = self.output_dir,
            file_name=(f"threshold_overlay_"
                       f"{self.settings.adm1}-"
                       f"{self.settings.adm2}-"
                       f"{self.settings.adm3}.txt_{scenario_name}"
                       ),
        )