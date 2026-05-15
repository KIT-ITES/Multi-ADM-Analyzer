import time

from multi_adm_analyzer.config.settings import Settings
from multi_adm_analyzer.geo.grid_joiner import GridJoiner
from multi_adm_analyzer.geo.grid_loader import GridLoader
from multi_adm_analyzer.data_io.cell_value_loader import CellValueLoader
from multi_adm_analyzer.data_io.json_writer import JsonWriter
from multi_adm_analyzer.data_io.scenario_discovery import ScenarioDiscovery
from multi_adm_analyzer.plotting.plot_context import PlotContext
from multi_adm_analyzer.stats.frequency import RelativeFrequencyCalculator
from multi_adm_analyzer.plotting.discrete_visualizer import DiscreteVisualizer
from multi_adm_analyzer.stats.intermodel_metrics import (
    InterModelMetricsCalculator,
    InterModelMetricsWriter,
)


class RelativeFrequencyPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings

        self.output_dir = settings.relative_output_dir()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.scenario_discovery = ScenarioDiscovery()
        self.grid_loader = GridLoader()
        self.grid_joiner = GridJoiner()
        self.json_writer = JsonWriter()
        self.frequency_calculator = RelativeFrequencyCalculator(event_threshold = settings.exceed_level, include_equal = True)

        self.intermodel_metrics_calculator = InterModelMetricsCalculator(comparison_domain = "union_nonzero")
        self.intermodel_metrics_writer = InterModelMetricsWriter()

    def run(self) -> None:
        start = time.time()

        print(f"[run] Using {self.settings.n_cpus} CPU cores")
        print(f"[run] Debug log writing: {self.settings.write_debug_logs}")

        grid = self.grid_loader.load(self.settings.grid_path)
        print(f"[run] Loaded grid with {len(grid)} cells.")

        scenarios = self.scenario_discovery.discover_common_scenarios(
            [
                self.settings.adm_paths_1(),
                self.settings.adm_paths_2(),
            ]
        )

        print(
            f"[run] Found {len(scenarios)} common scenarios for "
            f"{self.settings.adm1} and {self.settings.adm2}"
        )

        missing = self.scenario_discovery.report_missing_scenarios(
            [
                self.settings.adm_paths_1(),
                self.settings.adm_paths_2(),
            ]
        )

        for adm_name, missing_names in missing.items():
            if missing_names:
                print(f"[warning] {adm_name} is missing scenarios: {sorted(missing_names)}")

        for scenario in scenarios:
            first_path = scenario.paths_by_adm[self.settings.adm1]
            second_path = scenario.paths_by_adm[self.settings.adm2]

            self._run_scenario(scenario_name = scenario.name,
                               first_path = first_path,
                               second_path = second_path,
                               grid = grid)

        print(f"[run] Relative-frequency pipeline finished in {time.time() - start:.2f}s")

    def _run_scenario(self, scenario_name: str, first_path, second_path, grid) -> None:
        print(f"\n----====== {scenario_name} =====----")

        first_count = self.scenario_discovery.count_files(first_path)
        second_count = self.scenario_discovery.count_files(second_path)

        print(f"[run] found: {first_count} files in {first_path}")
        print(f"[run] found: {second_count} files in {second_path}")

        total_files = max(first_count, second_count)

        if total_files <= 0:
            print(f"[warning] Skipping {scenario_name}: no files found.")
            return

        worker_count = min(self.settings.n_cpus, 18)
        loader = CellValueLoader(workers = worker_count, chunk_size = 2)

        read_start = time.time()

        first_values = loader.load_folder(first_path)
        second_values = loader.load_folder(second_path)

        print(
            f"[run] Read both ADM folders in {time.time() - read_start:.2f}s. "
            f"Cells: {self.settings.adm1}={len(first_values)}, "
            f"{self.settings.adm2}={len(second_values)}"
        )

        result = self.frequency_calculator.compute(first_values_by_cell = first_values,
                                                   second_values_by_cell = second_values,
                                                   total_files = total_files)

        metrics = self.intermodel_metrics_calculator.compute(scenario_name = scenario_name,
                                                             first_model = self.settings.adm1,
                                                             second_model = self.settings.adm2,
                                                             first_frequency_by_cell = result.first_frequency_by_cell,
                                                             second_frequency_by_cell = result.second_frequency_by_cell)
        print("\n".join(metrics.to_lines()))

        self.intermodel_metrics_writer.append_csv(output_path = self.output_dir / "intermodel_metrics.csv", metrics = metrics)

        if self.settings.write_debug_logs:
            self.intermodel_metrics_writer.append_text(
                output_path = (
                        self.output_dir
                        / f"{scenario_name}_intermodel_metrics_"
                          f"{self.settings.adm1}-{self.settings.adm2}.txt"
                ),
                metrics = metrics,
            )

        if self.settings.write_debug_logs:
            self._write_debug_values(scenario_name = scenario_name,
                                     first_values = first_values,
                                     second_values = second_values,
                                     first_frequency_by_cell = result.first_frequency_by_cell,
                                     second_frequency_by_cell = result.second_frequency_by_cell,
                                     difference_by_cell = result.difference_by_cell,
                                     absolute_difference_by_cell = result.absolute_difference_by_cell)

        grid_diff = self.grid_joiner.attach_values(grid = grid,
                                                   values_by_cell = result.difference_by_cell,
                                                   value_column = "grid_class")

        min_cell, min_value, max_cell, max_value = self.grid_joiner.extrema(grid_diff)

        print(
            f"[Cells] Min: ({min_cell}, {min_value}) "
            f"Max: ({max_cell}, {max_value})"
        )

        self._plot_difference_map(scenario_name = scenario_name,
                                  grid_diff = grid_diff,
                                  min_cell = min_cell,
                                  min_value = min_value,
                                  max_cell = max_cell,
                                  max_value = max_value)

    def _write_debug_values(self, scenario_name: str,
                            first_values: dict[int, list[float]],
                            second_values: dict[int, list[float]],
                            first_frequency_by_cell: dict[int, float],
                            second_frequency_by_cell: dict[int, float],
                            difference_by_cell: dict[int, float],
                            absolute_difference_by_cell: dict[int, float]) -> None:
        self.json_writer.write(
            data = first_values,
            output_dir = self.output_dir,
            file_name = f"{self.settings.adm1}.txt_{scenario_name}",
        )

        self.json_writer.write(
            data = second_values,
            output_dir = self.output_dir,
            file_name = f"{self.settings.adm2}.txt_{scenario_name}",
        )

        self.json_writer.write(
            data = first_frequency_by_cell,
            output_dir = self.output_dir,
            file_name = f"frequency_{self.settings.adm1}.txt_{scenario_name}",
        )

        self.json_writer.write(
            data = second_frequency_by_cell,
            output_dir = self.output_dir,
            file_name = f"frequency_{self.settings.adm2}.txt_{scenario_name}",
        )

        self.json_writer.write(
            data = difference_by_cell,
            output_dir = self.output_dir,
            file_name = f"diff_{self.settings.adm1}-{self.settings.adm2}.txt_{scenario_name}",
        )

        self.json_writer.write(
            data = absolute_difference_by_cell,
            output_dir = self.output_dir,
            file_name = f"diff_abs_{self.settings.adm1}-{self.settings.adm2}.txt_{scenario_name}",
        )

    def _plot_difference_map(self, scenario_name: str, grid_diff,
                             min_cell: int, min_value: float,
                             max_cell: int, max_value: float,) -> None:

        plot_context = PlotContext.from_settings(self.settings)
        plot_context.save_dir = self.output_dir

        visualizer = DiscreteVisualizer(grid_diff, plot_context, scenario_name,
                                        sub_title = f"relative_freq_{self.settings.adm1}-{self.settings.adm2}")

        title = (
            f"{self.settings.adm1}-{self.settings.adm2} Difference Map - {scenario_name}. "
            f"Min Cell Value: {min_value:.4f}, Max Cell Value: {max_value:.4f}"
        )

        visualizer.set_plot_title(title)
        visualizer.set_legend_title("Relative Frequency")

        visualizer.set_highlighting_parameters(cells = [min_cell, max_cell], labels = ["Min Cell", "Max Cell"], colors = ["#d8d800", "black"])
        visualizer.highlight_cells()

        visualizer.set_bins_and_labels(mode = "zero_split", start = min_value, stop = max_value, count = 11)

        bbox_anchor = self._bbox_anchor_for(scenario_name)
        visualizer.set_bbox_to_anchor(bbox_anchor)

        visualizer.do_plotting()

    def _bbox_anchor_for(self, scenario_name: str) -> tuple[float, float]:
        key = f"{self.settings.adm1}-{self.settings.adm2}"

        try:
            params = self.settings.raw[key]["difference_plots_params"]
            value = (
                params[self.settings.site_name]
                .get("box_anchors")
                .get(scenario_name.lower())
            )

            if value is None:
                return 0.85, 0.75

            return tuple(value)

        except KeyError:
            return 0.85, 0.75