import time
from abc import ABC, abstractmethod
from typing import Mapping

from multi_adm_analyzer.config.settings import Settings
from multi_adm_analyzer.domain.overlay_mode import OverlayMode
from multi_adm_analyzer.geo.grid_joiner import GridJoiner
from multi_adm_analyzer.geo.grid_loader import GridLoader
from multi_adm_analyzer.data_io.cell_value_loader import CellValueLoader
from multi_adm_analyzer.data_io.json_writer import JsonWriter
from multi_adm_analyzer.data_io.scenario_discovery import ScenarioDiscovery
from multi_adm_analyzer.plotting.plot_context import PlotContext
from multi_adm_analyzer.stats.common import map_single_nonzero_run
from multi_adm_analyzer.stats.highlighting import SingleRunHighlighter
from multi_adm_analyzer.stats.overlay import OverlayClassifier, OverlayLabelBuilder
from multi_adm_analyzer.plotting.discrete_visualizer import DiscreteVisualizer


class BaseOverlayPipeline(ABC):
    COLORS_BY_FLAG = {
        1: "#951717",
        2: "#2b3acf",
        4: "#409344",
        3: "#c400c4",
        5: "#00d8d8",
        6: "#ffd555",
        7: "#3d3d3d",
    }

    def __init__(self, settings: Settings, mode: OverlayMode = OverlayMode.INTERSECTION):
        self.settings = settings
        self.mode = mode

        self.output_dir = settings.overlay_output_dir()
        self.output_dir.mkdir(parents = True, exist_ok = True)

        self.scenario_discovery = ScenarioDiscovery()
        self.grid_loader = GridLoader()
        self.grid_joiner = GridJoiner()
        self.json_writer = JsonWriter()

        self.overlay_classifier = OverlayClassifier(mode)
        self.label_builder = OverlayLabelBuilder()
        self.highlighter = SingleRunHighlighter()

    @property
    def enable_single_run_highlighting(self) -> bool:
        return False

    def run(self) -> None:
        start = time.time()

        print(f"[run] Using {self.settings.n_cpus} CPU cores")
        print(f"[run] Debug log writing: {self.settings.write_debug_logs}")

        grid = self.grid_loader.load(self.settings.grid_path)
        print(f"[run] Loaded grid with {len(grid)} cells.")

        adm_paths = [
            self.settings.adm_paths_1(),
            self.settings.adm_paths_2(),
            self.settings.adm_paths_3(),
        ]

        scenarios = self.scenario_discovery.discover_common_scenarios(adm_paths)

        print(f"[run] Found {len(scenarios)} common scenarios for "
              f"{self.settings.adm1}, {self.settings.adm2}, {self.settings.adm3}")

        missing = self.scenario_discovery.report_missing_scenarios(adm_paths)

        for adm_name, missing_names in missing.items():
            if missing_names:
                print(f"[warning] {adm_name} is missing scenarios: {sorted(missing_names)}")

        for scenario in scenarios:
            self._run_scenario(scenario, grid)

        print(f"[run] {self.pipeline_label} finished in {time.time() - start:.2f}s")

    def _run_scenario(self, scenario, grid) -> None:
        scenario_name = scenario.name
        print(f"\n----====== {scenario_name} =====----")

        paths = {
            self.settings.adm1: scenario.paths_by_adm[self.settings.adm1],
            self.settings.adm2: scenario.paths_by_adm[self.settings.adm2],
            self.settings.adm3: scenario.paths_by_adm[self.settings.adm3],
        }

        for adm_name, path in paths.items():
            count = self.scenario_discovery.count_files(path)
            print(f"[run] found: {count} files in {path} for {adm_name}")

        loader = CellValueLoader(
            workers = min(self.settings.n_cpus, 18),
            chunk_size = 2,
        )

        read_start = time.time()

        values_by_adm = {
            self.settings.adm1: loader.load_folder(paths[self.settings.adm1]),
            self.settings.adm2: loader.load_folder(paths[self.settings.adm2]),
            self.settings.adm3: loader.load_folder(paths[self.settings.adm3]),
        }

        print(
            f"[run] Read all ADM folders in {time.time() - read_start:.2f}s. "
            f"Cells: {self.settings.adm1}={len(values_by_adm[self.settings.adm1])}, "
            f"{self.settings.adm2}={len(values_by_adm[self.settings.adm2])}, "
            f"{self.settings.adm3}={len(values_by_adm[self.settings.adm3])}"
        )

        presence_by_adm = self._build_presence_maps(scenario_name = scenario_name,
                                                    grid = grid,
                                                    values_by_adm = values_by_adm)

        overlay_result = self.overlay_classifier.classify(first_cells = presence_by_adm[self.settings.adm1],
                                                          second_cells = presence_by_adm[self.settings.adm2],
                                                          third_cells = presence_by_adm[self.settings.adm3])

        highlighting_by_cell: dict[int, int] = {}

        if self.enable_single_run_highlighting:
            single_run_by_adm = {adm_name: map_single_nonzero_run(values) for adm_name, values in values_by_adm.items() }

            highlighting_by_cell = self.highlighter.extract_matching_single_run_cells(first_single_run_by_cell = single_run_by_adm[self.settings.adm1],
                                                                                      second_single_run_by_cell = single_run_by_adm[self.settings.adm2],
                                                                                      third_single_run_by_cell = single_run_by_adm[self.settings.adm3],
                                                                                      candidate_cells = set(overlay_result.flags_by_cell.keys()),
            )

        for flag, count in sorted(overlay_result.counts_by_flag.items()):
            print(f"[Category {flag}]: found {count} cells")

        if self.settings.write_debug_logs:
            self._write_debug_values(scenario_name = scenario_name,
                                     values_by_adm = values_by_adm,
                                     presence_by_adm = presence_by_adm,
                                     flags_by_cell = overlay_result.flags_by_cell)

        grid_overlay = self.grid_joiner.attach_values(grid = grid,
                                                      values_by_cell = overlay_result.flags_by_cell,
                                                      value_column = "grid_class")

        valid = grid_overlay["grid_class"].notna().sum()
        print(f"[run] Attached overlay flags for {valid} cells.")

        self._plot_overlay_map(scenario_name = scenario_name,
                               grid_overlay = grid_overlay,
                               highlighting_by_cell = highlighting_by_cell
        )

    @abstractmethod
    def _build_presence_maps(self, scenario_name: str, grid, values_by_adm: Mapping[str, dict[int, list[float]]]) -> dict[str, Mapping[int, object]]:
        pass

    @abstractmethod
    def _write_debug_values(self, scenario_name: str, values_by_adm: Mapping[str, dict[int, list[float]]],
                            presence_by_adm: Mapping[str, Mapping[int, object]],
                            flags_by_cell: dict[int, int],) -> None:
        pass

    @property
    @abstractmethod
    def pipeline_label(self) -> str:
        pass

    @property
    @abstractmethod
    def output_subtitle_prefix(self) -> str:
        pass

    def _plot_overlay_map(self, scenario_name: str, grid_overlay, highlighting_by_cell: dict[int, int]) -> None:

        plot_context = PlotContext.from_settings(self.settings)
        plot_context.save_dir = self.output_dir

        threshold_text = (f"{int(self.settings.threshold * 100)}% Threshold "
                          if self.settings.threshold != 0.0
                          else "")

        title = (f"{self.settings.adm1}—{self.settings.adm2}—{self.settings.adm3} "
                 f"{threshold_text}{self.mode.name.title()} Map - {scenario_name}")

        legend_title = "Overlay Combinations"
        if threshold_text:
            legend_title += f"\n({threshold_text.rstrip()})"

        sub_title = (f"{self.output_subtitle_prefix}"
                     f"{self.mode.name.lower()}_"
                     f"{self.settings.adm1}-{self.settings.adm2}-{self.settings.adm3}"
        )

        visualizer = DiscreteVisualizer(grid_overlay, plot_context, scenario_name, sub_title = sub_title)

        visualizer.set_plot_title(title)
        visualizer.set_legend_title(legend_title)

        bins = self.label_builder.bins_for_mode(self.mode)

        labels_by_flag = self.label_builder.build_labels(adm1 = self.settings.adm1,
                                                         adm2 = self.settings.adm2,
                                                         adm3 = self.settings.adm3)

        labels = [labels_by_flag[bins[index + 1]] for index in range(len(bins) - 1)]
        colors = [self.COLORS_BY_FLAG[bins[index + 1]] for index in range(len(bins) - 1)]

        visualizer.set_bins_and_labels(mode = "custom", bins = bins, labels = labels)
        visualizer.set_colors(colors = colors)

        highlight_cells = list(highlighting_by_cell.keys())
        highlight_days = list(highlighting_by_cell.values())

        if highlight_cells:
            visualizer.set_highlighting_parameters(cells = highlight_cells, labels = "One Run", colors = "black", text = highlight_days)
            visualizer.highlight_cells(line_style = "solid")

        visualizer.set_bbox_to_anchor(self._bbox_anchor_for(scenario_name))
        visualizer.do_plotting()

    def _bbox_anchor_for(self, scenario_name: str) -> tuple[float, float]:
        key = f"{self.settings.adm1}-{self.settings.adm2}-{self.settings.adm3}"
        plot_key = f"{self.mode.name.lower()}_plots_params"

        try:
            value = (
                self.settings.raw[key][plot_key][self.settings.site_name]
                .get("box_anchors")
                .get(scenario_name.lower())
            )
            return tuple(value) if value is not None else (0.85, 0.75)
        except KeyError:
            return 0.85, 0.75