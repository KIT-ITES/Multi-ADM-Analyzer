import gc
from typing import Any

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from multi_adm_analyzer.plotting.visualizer import Visualizer


class DiscreteVisualizer(Visualizer):
    DEFAULT_COLORS = [
        "#2b3acf",
        "#7482cf",
        "#2196F3",
        "#00dffb",
        "#409344",
        "#81c884",
        "#ffd555",
        "#ffe8a3",
        "#d78000",
        "#ffa284",
        "#E53935",
        "#951717",
    ]

    def __init__(self, grid, plot_context: Any, name: str, **save_params):
        grid_copy = grid.copy(deep = True)

        print("[CRS] before transformation", grid_copy.crs)

        grid_projected = grid_copy.to_crs(epsg = plot_context.epsg)

        print("[CRS] after transformation", grid_projected.crs)

        super().__init__(grid_projected, plot_context, name)

        self.sub_title = save_params["sub_title"]

        self._bins: np.ndarray | None = None
        self._labels: list[str] | None = None
        self._colors = list(self.DEFAULT_COLORS)
        self._cmap = ListedColormap(self._colors)

        self._alpha_value = 0.8
        self._line_style: str | None = None
        self._bbox_to_anchor: tuple[float, float] = (0.85, 0.75)

        self._highlighting_cells: list[int] | None = None
        self._highlighting_labels: list[str] | None = None
        self._highlighting_colors: list[str] | None = None
        self._highlighting_text: list[Any] | None = None

    def set_bins_and_labels(self, mode: str = "zero_split", **kwargs) -> None:
        if not {"start", "stop", "count", "bins"}.intersection(kwargs.keys()):
            raise ValueError("Missing bin parameters")

        mode = mode.lower()

        if mode == "zero_split":
            self._set_zero_split_bins_and_labels(**kwargs)
        elif mode == "uniform":
            self._set_uniform_bins_and_labels(**kwargs)
        elif mode == "custom":
            self._set_custom_bins(**kwargs)

            labels = kwargs.get("labels")
            if labels is not None:
                self._set_custom_labels(labels)
        else:
            raise ValueError(f"Unsupported binning mode: {mode!r}")

    def set_colors(self, **kwargs) -> None:
        if "colors" in kwargs and isinstance(kwargs["colors"], list):
            self._colors = kwargs["colors"]
        else:
            start = kwargs.get("start", 0.1)
            stop = kwargs.get("stop", 1.0)

            if self._bins is None:
                raise RuntimeError("Bins must be configured before generated colors are used")

            self._colors = list(plt.cm.Spectral(np.linspace(start, stop, len(self._bins))))

        self._cmap = ListedColormap(self._colors)

        print("[Colors]", len(self._colors))

    def set_bbox_to_anchor(self, bbox_to_anchor: tuple[float, float]) -> None:
        self._bbox_to_anchor = bbox_to_anchor

    def get_ax(self):
        return self.ax

    def do_plotting(self) -> None:
        self.plot_grid()

        self.assign_distance_axes_km()
        self.apply_map_extent()
        self.add_basemap_overlay()

        self.add_distance_axes_km()
        self.add_plot_title()

        self.apply_map_extent()
        self.draw_with_polar_reference()

        handles = self.build_legend_handles()

        if self.context.show_legend:
            self.draw_legend(handles)

        if self.context.export_legend:
            self.save_legend_figure(handles)

        plt.tight_layout()

        del self.grid_web_mercator
        gc.collect()

        self.save_probability_plots(self.context.save_dir,
                                    self.name,
                                    self.sub_title)

    def plot_grid(self) -> None:
        self.grid_web_mercator.plot(column = "class",
                                    ax = self.ax,
                                    cmap = self._cmap,
                                    edgecolor = "none",
                                    linewidth = 0,
                                    alpha = self._alpha_value,
                                    categorical = False,
                                    legend = False,
                                    vmin = 0,
                                    vmax = len(self._colors) - 1,
                                    missing_kwds = {"color": "lightgrey", "alpha": 0},
                                    zorder = 5,)

        self.draw_site_location()

    def attach_labels_and_bins_to_grid(self, zero_eps: float = 1e-8) -> None:
        if self._bins is None:
            raise RuntimeError("Bins are not configured")

        values = self.grid_web_mercator["grid_class"].astype(float)
        bins = np.asarray(self._bins, dtype=float)

        negative_edges = bins[bins < 0]
        positive_edges = bins[bins > 0]

        if len(negative_edges) == 0 or len(positive_edges) == 0:
            raise RuntimeError("Zero-split bins must include both negative and positive values")

        last_negative = negative_edges[-1]
        first_positive = positive_edges[0]

        intervals: list[tuple[float, float]] = []

        for index in range(len(negative_edges) - 1):
            intervals.append((negative_edges[index], negative_edges[index + 1]))

        intervals.append((last_negative, 0.0))
        intervals.append((0.0, 0.0))
        intervals.append((0.0, first_positive))

        for index in range(len(positive_edges) - 1):
            intervals.append((positive_edges[index], positive_edges[index + 1]))

        codes = np.full(len(values), -1, dtype=int)

        for index, (left, right) in enumerate(intervals):
            if left == 0.0 and right == 0.0:
                mask = np.isclose(values, 0.0, atol=zero_eps)
            elif right == 0.0:
                mask = (values > left) & (values < 0)
            elif left == 0.0:
                mask = (values > 0) & (values <= right)
            else:
                mask = (values > left) & (values <= right)

            codes[mask] = index

        labels = [self._format_interval_label(left, right) for left, right in intervals]

        self.grid_web_mercator["class"] = pd.Categorical.from_codes(codes,
                                                                    categories = labels,
                                                                    ordered = True)

        self._labels = labels

        print("[final intervals]", np.array(intervals).tolist())
        print("[Intervals of length]", len(intervals))
        print("[final categories]", labels)
        print("[categories of length]", len(labels))
        print("[zeros assigned to]", int(np.sum(codes == intervals.index((0.0, 0.0)))), "values")

    def attach_custom_labels_and_bins_to_grid(self) -> None:
        if self._bins is None:
            raise RuntimeError("Bins are not configured")

        if self._labels is None:
            raise RuntimeError("Labels are not configured")

        data_min, data_max = self.grid_web_mercator["grid_class"].agg(["min", "max"])

        print(f"[run] data_min, data_max in grid: {data_min:.6f}, {data_max:.6f}")

        self.grid_web_mercator["class"] = pd.cut(self.grid_web_mercator["grid_class"],
                                                 bins = self._bins,
                                                 labels = self._labels,
                                                 include_lowest = False,
                                                 right = True)

    def build_legend_handles(self):
        if self._labels is None:
            raise RuntimeError("Labels are not configured")

        legend_elements = [
            Patch(
                facecolor = self._colors[index],
                edgecolor = "none",
                label = self._labels[index],
                alpha = self._alpha_value,
            )
            for index in range(len(self._labels))
        ][::-1]

        site_marker = Line2D(
            [0],
            [0],
            marker = "x",
            color = "black",
            markersize = 7,
            linewidth = 0.0,
            markeredgewidth = 1.1,
            alpha = 0.9,
            label = f"{getattr(self.context, 'site_name', 'Site')} NPP",
        )

        highlighted_cells_legend = []

        if self._highlighting_labels is not None:
            for index, label in enumerate(self._highlighting_labels):
                color = (
                    self._highlighting_colors[index]
                    if self._highlighting_colors and len(self._highlighting_colors) > 1
                    else self._highlighting_colors[0]
                )

                highlighted_cells_legend.append(
                    Line2D(
                        [0],
                        [0],
                        color = color,
                        linestyle = self._line_style,
                        linewidth = 1.2,
                        alpha = 0.9,
                        label = label,
                    )
                )

        return [site_marker] + highlighted_cells_legend + legend_elements

    def draw_legend(self, handles) -> None:
        self.ax.legend(
            handles = handles,
            title = self.legend_title,
            loc = "upper left",
            bbox_to_anchor = self._bbox_to_anchor,
            fontsize = self.context.font_size_legend,
            title_fontsize = self.context.font_size_legend_title,
            frameon = self.context.legend_frame,
            handleheight = 1.5,
            borderpad = 1.2,
        )

    def save_legend_figure(self, handles) -> None:
        legend_fig = plt.figure(figsize = (4.0, 6.0))
        legend_ax = legend_fig.add_subplot(111)
        legend_ax.axis("off")

        legend_ax.legend(
            handles = handles,
            title = self.legend_title,
            loc = "center",
            fontsize = self.context.font_size_legend,
            title_fontsize = self.context.font_size_legend_title,
            frameon = self.context.legend_frame,
        )

        output_base = self.context.save_dir / f"{self.name}_{self.sub_title}_legend"

        legend_fig.savefig(output_base.with_suffix(".png"),
                           dpi = self.context.dpi,
                           bbox_inches = "tight")

        legend_fig.savefig(output_base.with_suffix(".pdf"),
                           bbox_inches = "tight")

        plt.close(legend_fig)

    def highlight_cells(self, line_width: float = 0.4, line_style: str = "--") -> None:
        if self._highlighting_cells is None:
            return

        if all(cell is None for cell in self._highlighting_cells):
            return

        self._line_style = line_style

        colorable_indexes = [
            index
            for index, value in enumerate(self._highlighting_cells)
            if value is not None
        ]

        if self._highlighting_colors is None:
            generated_colors = plt.cm.Spectral(np.linspace(0.1, 1, len(colorable_indexes)))
            self._highlighting_colors = list(ListedColormap(generated_colors).colors)

        grid = self.grid_web_mercator
        cell_column = "Cell" if "Cell" in grid.columns else "cell_id"

        cell_ids = [cell for cell in self._highlighting_cells if cell is not None]

        for color_index, cell_id in zip(colorable_indexes, cell_ids):
            geometry = self._get_cell_geometry(cell_column, cell_id, grid)
            x, y = geometry.exterior.xy

            color = (
                self._highlighting_colors[color_index]
                if len(self._highlighting_colors) > 1
                else self._highlighting_colors[0]
            )

            self.ax.plot(x, y,
                         linestyle = self._line_style,
                         color = color,
                         linewidth = line_width,
                         alpha = 0.8,
                         zorder = 6,)

            if self._highlighting_text is not None:
                centroid = geometry.centroid

                text = (
                    self._highlighting_text[color_index]
                    if len(self._highlighting_text) > 1
                    else self._highlighting_text[0]
                )

                self.ax.text(
                    centroid.x,
                    centroid.y,
                    str(text),
                    ha = "center",
                    va = "center",
                    fontsize = 1,
                    color = "black",
                    zorder = 6,
                    bbox = {
                        "facecolor": "white",
                        "alpha": 0.0,
                        "edgecolor": "none",
                    },
                )

    def set_highlighting_parameters(self, cells, labels = None, colors = None, text = None,) -> None:
        if cells is not None and not isinstance(cells, list):
            cells = [cells]

        if labels is not None and not isinstance(labels, list):
            labels = [labels]

        if colors is not None and not isinstance(colors, list):
            colors = [colors]

        if text is not None and not isinstance(text, list):
            text = [text]

        if labels is not None and colors is None:
            raise ValueError("Colors must be given with labels")

        self._highlighting_cells = cells
        self._highlighting_labels = labels
        self._highlighting_colors = colors
        self._highlighting_text = text

    def _set_zero_split_bins_and_labels(self, *,
                                        start = None, stop = None,
                                        count: int = 11) -> None:
        eps = 1e-12

        data_min, data_max = self.grid_web_mercator["grid_class"].agg(["min", "max"])

        start = float(data_min) if start is None else float(start)
        stop = float(data_max) if stop is None else float(stop)

        negative_count = count // 2
        positive_count = count - negative_count

        negative_bins = np.linspace(start - eps, 0.0, negative_count + 1, endpoint=True)
        positive_bins = np.linspace(0.0, stop + eps, positive_count + 1, endpoint=True)

        raw_bins = np.unique(np.concatenate([negative_bins, positive_bins]))

        print(f"[bins] using range ({raw_bins[0]:.4f}, {raw_bins[-1]:.4f}) "
              f"with {len(raw_bins) - 1} intervals.")
        print("[Zero-split bins]", raw_bins)

        self._bins = self._ensure_single_zero_entry(raw_bins, eps)
        self._labels = None

        print("[bins after cleaning]", self._bins)

        self.attach_labels_and_bins_to_grid()

    def _set_uniform_bins_and_labels(self, **kwargs) -> None:
        eps = 1e-12

        data_min, data_max = self.grid_web_mercator["grid_class"].agg(["min", "max"])

        start = float(kwargs.get("start", data_min))
        stop = float(kwargs.get("stop", data_max))
        count = int(kwargs.get("count", 11))

        raw_bins = np.linspace(start - eps, stop + eps, count)

        print(
            f"[bins] using range ({raw_bins[0]:.4f}, {raw_bins[-1]:.4f}) "
            f"with {len(raw_bins) - 1} intervals."
        )
        print("[raw bins]", raw_bins)

        self._bins = self._ensure_single_zero_entry(raw_bins, eps)
        self._labels = None

        print("[bins after Zero]", self._bins)
        print("[Labels]", "setting normalised labels with zero interval")

        self.attach_labels_and_bins_to_grid()

    def _set_custom_bins(self, **kwargs) -> None:
        bins = kwargs.get("bins")
        labels = kwargs.get("labels")

        if bins is None or not isinstance(bins, list):
            raise ValueError("Missing or invalid bins definition")

        self._bins = np.array(sorted(set(map(float, bins))))

        print(
            f"[bins] Using user-defined bins ({self._bins[0]:.4f}, {self._bins[-1]:.4f}) "
            f"[{len(self._bins) - 1} intervals]"
        )

        if labels is None:
            self._labels = [
                f"({self._bins[index]:.2f}, {self._bins[index + 1]:.2f}]"
                for index in range(len(self._bins) - 1)
            ]

            print("[labels]", self._labels)
            self.attach_custom_labels_and_bins_to_grid()

    def _set_custom_labels(self, labels: list[str]) -> None:
        self._labels = labels

        print("[labels]", self._labels)

        self.attach_custom_labels_and_bins_to_grid()

    @staticmethod
    def _ensure_single_zero_entry(bins: np.ndarray, eps: float) -> np.ndarray:
        normalized = np.where(np.isclose(bins, 0.0, atol=eps), 0.0, bins)
        unique_bins = np.unique(normalized)

        if not np.any(unique_bins == 0.0):
            index = np.searchsorted(unique_bins, 0.0)
            unique_bins = np.insert(unique_bins, index, 0.0)

        return unique_bins

    @staticmethod
    def _format_interval_label(left: float, right: float) -> str:
        if left == 0.0 and right == 0.0:
            return "[0, 0]"

        if right == 0.0:
            return f"({left:.4f}, 0)"

        if left == 0.0:
            return f"(0, {right:.4f}]"

        return f"({left:.4f}, {right:.4f}]"

    @staticmethod
    def _get_cell_geometry(cell_column: str, cell_id: int, grid) -> Any:
        row = grid.loc[grid[cell_column] == cell_id]

        if row.empty:
            raise KeyError(f"Cell {cell_id} not found in grid column {cell_column!r}")

        return row.iloc[0].geometry