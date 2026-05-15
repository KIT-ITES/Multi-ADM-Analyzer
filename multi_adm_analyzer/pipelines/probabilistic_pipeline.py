import time
from pathlib import Path

from multi_adm_analyzer.config.settings import Settings
from multi_adm_analyzer.geo.grid_joiner import GridJoiner
from multi_adm_analyzer.geo.grid_loader import GridLoader
from multi_adm_analyzer.data_io.scenario_discovery import ScenarioDiscovery
from multi_adm_analyzer.data_io.json_writer import JsonWriter
from multi_adm_analyzer.data_io.cell_value_loader import CellValueLoader
from multi_adm_analyzer.plotting.plot_context import PlotContext
from multi_adm_analyzer.stats.common import build_absolute_counts
from multi_adm_analyzer.stats.exceedance import ExceedanceCalculator
from multi_adm_analyzer.stats.statistics_writer import StatisticsWriter
from multi_adm_analyzer.plotting.discrete_visualizer import DiscreteVisualizer


class ProbabilisticPipeline:
    COLORS = [
        "#2b3acf",
        "#7482cf",
        "#2196F3",
        "#00dffb",
        "#409344",
        "#ffd555",
        "#d78000",
        "#ffa284",
        "#E53935",
        "#951717",
    ]

    PROBABILITY_BINS = [
        0.0,
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        1.0,
    ]

    def __init__(self, settings: Settings):
        self.settings = settings

        self.output_dir = settings.probabilistic_output_dir()
        self.output_dir.mkdir(parents = True, exist_ok = True)

        self.scenario_discovery = ScenarioDiscovery()
        self.grid_loader = GridLoader()
        self.grid_joiner = GridJoiner()
        self.json_writer = JsonWriter()
        self.statistics_writer = StatisticsWriter()

        self.exceedance_calculator = ExceedanceCalculator(exceed_level = settings.exceed_level,
                                                          threshold = settings.threshold)

    def run(self) -> None:
        start = time.time()

        print(f"[run] Using {self.settings.n_cpus} CPU cores")
        print(f"[run] Debug log writing: {self.settings.write_debug_logs}")

        grid = self.grid_loader.load(self.settings.grid_path)
        print(f"[run] Loaded grid with {len(grid)} cells.")

        scenarios = self.scenario_discovery.discover_single_adm(self.settings.adm_paths_1())

        print(f"[run] Found {len(scenarios)} scenarios for {self.settings.adm1}")

        for scenario in scenarios:
            self._run_scenario(scenario.name, scenario.paths_by_adm[self.settings.adm1], grid)

        print(f"[run] Probabilistic pipeline finished in {time.time() - start:.2f}s")

    def _run_scenario(self, scenario_name: str, scenario_path: Path, grid) -> None:
        print(f"\n----====== {scenario_name} =====----")

        scenario_start = time.time()
        file_count = self.scenario_discovery.count_files(scenario_path)

        print(f"[run] Found {file_count} files in {scenario_path}")

        worker_count = min(self.settings.n_cpus, 18)
        loader = CellValueLoader(workers = worker_count, chunk_size = 2)

        values_by_cell = loader.load_folder(scenario_path)

        print(
            f"[run] Read files in {time.time() - scenario_start:.2f}s. "
            f"Found data for {len(values_by_cell)} cells."
        )

        if self.settings.write_debug_logs:
            self._write_debug_values(scenario_name = scenario_name,
                                     values_by_cell = values_by_cell)

        grid_prob = self._compute_probability_grid(scenario_name = scenario_name,
                                                   grid = grid,
                                                   values_by_cell = values_by_cell)

        min_cell, min_value, max_cell, max_value = self.grid_joiner.extrema(grid_prob)

        print(
            f"[Cells] Min: ({min_cell}, {min_value}) "
            f"Max: ({max_cell}, {max_value})"
        )

        self._plot_probability_map(scenario_name = scenario_name,
                                   grid_prob = grid_prob,
                                   max_cell = max_cell,
                                   max_value = max_value,
        )

    def _write_debug_values(self, scenario_name: str, values_by_cell: dict[int, list[float]]) -> None:
        print("[run] Saving values to file")

        self.json_writer.write(
            data = values_by_cell,
            output_dir = self.output_dir,
            file_name = f"{self.settings.adm1}.txt_{scenario_name}",
        )

        absolute_counts = build_absolute_counts(values_by_cell)

        self.json_writer.write(
            data = absolute_counts,
            output_dir = self.output_dir,
            file_name = f"absolute_{self.settings.adm1}.txt_{scenario_name}",
        )

        print(
            f"[run] Created absolute values for {len(absolute_counts)} cells. "
            "Saved absolute values to file."
        )

    def _compute_probability_grid(self, scenario_name: str, grid, values_by_cell: dict[int, list[float]]):
        print(
            f"\nComputing exceedance probabilities for "
            f"exceed_level = {self.settings.exceed_level}..."
        )

        cell_column = "Cell" if "Cell" in grid.columns else "cell_id"
        cell_ids = [int(cell) for cell in grid[cell_column]]

        result = self.exceedance_calculator.compute(values_by_cell = values_by_cell,
                                                    cell_ids = cell_ids)

        summary_lines = result.summary.to_lines(title = "Exceedance probability statistics excluding 0 and NaN")
        print("\n".join(summary_lines))

        if self.settings.write_debug_logs:
            statistics_path = (self.output_dir / f"{scenario_name}_statistical_data_{self.settings.adm1}.txt")

            self.statistics_writer.append_lines(statistics_path,
                                                summary_lines)

        return self.grid_joiner.attach_values(grid = grid,
                                              values_by_cell = result.probabilities_by_cell,
                                              value_column = "grid_class")

    def _plot_probability_map(self, scenario_name: str, grid_prob, max_cell: int, max_value: float,) -> None:
        plot_context = PlotContext.from_settings(self.settings)
        plot_context.save_dir = self.output_dir

        sub_title = (
            f"prop_map_{self.settings.adm1}"
            if self.settings.threshold == 0
            else f"{self.settings.threshold * 100:.2f}%_threshold_prop_map_{self.settings.adm1}"
        )

        title = (
            f"{self.settings.adm1} - {scenario_name} — Probabilistic Map"
            if self.settings.threshold == 0
            else (
                f"{self.settings.adm1} - {scenario_name} — "
                f"{int(self.settings.threshold * 100)}% Threshold Probabilistic Map"
            )
        )

        visualizer = DiscreteVisualizer(grid_prob, plot_context, scenario_name, sub_title = sub_title)

        visualizer.set_plot_title(f"{title}. Max Cell Value: {max_value:.4f}")
        visualizer.set_legend_title("Frequency Intervals")

        visualizer.set_highlighting_parameters(max_cell, "Max Cell", "black")
        visualizer.highlight_cells()

        visualizer.set_bins_and_labels(mode = "custom", bins = self.PROBABILITY_BINS)
        visualizer.set_colors(colors = self.COLORS)

        bbox_anchor = self._bbox_anchor_for(scenario_name)
        visualizer.set_bbox_to_anchor(bbox_anchor)

        visualizer.do_plotting()

    def _bbox_anchor_for(self, scenario_name: str) -> tuple[float, float]:
        plot_params = self.settings.raw[self.settings.adm1]["probabilistic_plots_params"]

        try:
            value = (
                plot_params[self.settings.site_name]
                .get("box_anchors")
                .get(scenario_name.lower())
            )

            if value is None:
                return 0.85, 0.75

            return tuple(value)

        except KeyError:
            return 0.85, 0.75