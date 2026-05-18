import gc
from pathlib import Path
from typing import Any

import contextily as cx
import geopandas as gpd
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from shapely import Point
from shapely.geometry import box


class Visualizer:

    @property
    def epsg(self) -> int:
        return self.context.epsg

    def __init__(self, grid_web_mercator, plot_context: Any, name: str):
        self.grid_web_mercator = grid_web_mercator
        self.context = plot_context
        self.name = name

        self.legend_title = ""
        self.plot_title = ""

        result_plot_params = plot_context.visual_parameters.get(name.lower())

        if result_plot_params is None:
            raise KeyError(f"No visual parameters configured for scenario {name!r}. "
                           f"Expected key: {name.lower()!r}")

        self.result_plot_params = result_plot_params

        self.major_step_km = result_plot_params["major_step_km"]
        self.minor_step_km = result_plot_params["minor_step_km"]
        self.ring_step_km = result_plot_params["ring_step_km"]
        self.max_radius_km = result_plot_params["max_radius_km"]
        self.show_bearings = result_plot_params["show_bearings"]
        self.bearing_step_deg = result_plot_params["bearing_step_deg"]
        self.padding_km = result_plot_params["padding_km"]

        self.fig, self.ax = plt.subplots(figsize = plot_context.figure_size)

    def add_distance_axes_km(self) -> None:
        site_x, site_y = self._release_site_projected()

        xmin, xmax = self.ax.get_xlim()
        ymin, ymax = self.ax.get_ylim()

        x_min_km = (xmin - site_x) / 1000
        x_max_km = (xmax - site_x) / 1000
        y_min_km = (ymin - site_y) / 1000
        y_max_km = (ymax - site_y) / 1000

        x_major_km = self._aligned_ticks(x_min_km, x_max_km, self.major_step_km)
        y_major_km = self._aligned_ticks(y_min_km, y_max_km, self.major_step_km)
        x_minor_km = self._aligned_ticks(x_min_km, x_max_km, self.minor_step_km)
        y_minor_km = self._aligned_ticks(y_min_km, y_max_km, self.minor_step_km)

        self.ax.set_xticks(site_x + x_major_km * 1000)
        self.ax.set_yticks(site_y + y_major_km * 1000)

        self.ax.set_xticks(site_x + x_minor_km * 1000, minor = True)
        self.ax.set_yticks(site_y + y_minor_km * 1000, minor = True)

        self.ax.set_xticklabels([f"{int(v)}" for v in x_major_km], fontsize = self.context.font_size_tick_label,)
        self.ax.set_yticklabels([f"{int(v)}" for v in y_major_km], fontsize = self.context.font_size_tick_label,)

        self.ax.set_xlabel("Distance West / East (km)", fontsize = self.context.font_size_axis_label)
        self.ax.set_ylabel("Distance South / North (km)", fontsize = self.context.font_size_axis_label)

        self.ax.set_aspect("equal")

    def draw_with_polar_reference(self) -> None:
        site_x, site_y = self._release_site_projected()

        self._draw_distance_rings(site_x, site_y)
        self._label_distance_rings(site_x, site_y)

        if self.show_bearings:
            self._draw_bearing_rays(site_x, site_y)

        self.ax.set_aspect("equal")

    def assign_distance_axes_km(self) -> None:
        site = gpd.GeoSeries(
            [Point(self.context.site_coord)],
            crs = "EPSG:4326",
        ).to_crs(self.grid_web_mercator.crs).iloc[0]

        grid = self.grid_web_mercator
        grid["dx_km"] = (grid.geometry.centroid.x - site.x) / 1000.0
        grid["dy_km"] = (grid.geometry.centroid.y - site.y) / 1000.0

        self.grid_web_mercator = grid

    def crop_to_attached_classes(self) -> None:
        grid = self.grid_web_mercator

        if "grid_class" not in grid.columns:
            print("grid_class column not found – cannot auto-crop.")
            return

        classified = grid[grid["grid_class"].notna()]

        if classified.empty:
            print("No classified cells to crop to.")
            return

        minx, miny, maxx, maxy = classified.total_bounds

        padding_m = float(self.padding_km) * 1000.0

        self.ax.set_xlim(minx - padding_m, maxx + padding_m)
        self.ax.set_ylim(miny - padding_m, maxy + padding_m)

    def add_basemap_overlay(self) -> None:
        if self.context.with_local_basemap_overlay:
            self._plot_local_basemap()
        else:
            self._plot_contextily_basemap()

    def draw_site_location(self) -> None:
        site_x, site_y = self._release_site_projected()

        self.ax.scatter(site_x,
                        site_y,
                        marker = "x",
                        s = 45,
                        color = "black",
                        linewidths = 0.6,
                        zorder = 10,
                        alpha = 0.5)

    def save_probability_plots(self, save_dir: str | Path, name: str, sub_title: str) -> None:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        base_name = f"{name}_{sub_title}"

        formats = ["png", "pdf"]
        paths = {}

        for fmt in formats:
            path = save_dir / f"{base_name}.{fmt}"
            kwargs = {"bbox_inches": "tight"}

            if fmt in {"png", "tiff"}:
                kwargs["dpi"] = self.context.dpi

            self.fig.savefig(path, format = fmt, **kwargs)
            paths[fmt] = path

        print("Saved maps to:")
        for fmt, path in paths.items():
            print(f"  {fmt}: {path}")

        plt.close(self.fig)

        del self.fig
        gc.collect()

    def set_plot_title(self, plot_title: str) -> None:
        self.plot_title = plot_title

    def set_legend_title(self, legend_title: str) -> None:
        self.legend_title = legend_title

    def add_plot_title(self) -> None:
        self.ax.set_title(self.plot_title,
                          fontsize = self.context.font_size_title,
                          fontweight = "bold",
                          pad = 10)

    def _release_site_projected(self) -> tuple[float, float]:
        point_gdf = gpd.GeoDataFrame(
            geometry=[Point(self.context.site_coord)],
            crs = "EPSG:4326",
        ).to_crs(epsg = self.epsg)

        site_x = float(point_gdf.geometry.x.iloc[0])
        site_y = float(point_gdf.geometry.y.iloc[0])

        return site_x, site_y

    @staticmethod
    def _aligned_ticks(min_val: float, max_val: float, step: float) -> np.ndarray:
        start = np.floor(min_val / step) * step
        end = np.ceil(max_val / step) * step
        return np.arange(start, end + step, step)

    def _draw_distance_rings(self, site_x: float, site_y: float) -> None:
        for dist_km in range(self.ring_step_km,
                             self.max_radius_km + self.ring_step_km,
                             self.ring_step_km
                             ):
            self.ax.add_patch(plt.Circle((site_x, site_y),
                                         dist_km * 1000.0,
                                         fill = False,
                                         linestyle = ":",
                                         linewidth = 0.6,
                                         edgecolor = "0.5",
                                         alpha = 0.6,
                                         zorder = 1))

    def _label_distance_rings(self, site_x: float, site_y: float) -> None:
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        frame_width = xlim[1] - xlim[0]
        frame_height = ylim[1] - ylim[0]
        frame_size = max(frame_width, frame_height)

        offset_m = 0.006 * frame_size
        margin = 0.004 * frame_size

        renderer = self.ax.figure.canvas.get_renderer()

        for dist_km in range(
            self.ring_step_km,
            self.max_radius_km + self.ring_step_km,
            self.ring_step_km,
        ):
            r_m = dist_km * 1000.0
            label = f"{dist_km}"

            distance_axis_offset = 0.01 * frame_size

            candidates = [
                (site_x + r_m + offset_m, site_y - distance_axis_offset, "left", "center"),
                (site_x - r_m - offset_m, site_y + distance_axis_offset, "right", "center"),
                (site_x + distance_axis_offset, site_y + r_m + offset_m, "left", "bottom"),
                (site_x - 4*distance_axis_offset, site_y - r_m - offset_m, "left", "top"),
            ]

            for x, y, ha, va in candidates:
                if not (
                    xlim[0] - frame_size <= x <= xlim[1] + frame_size
                    and ylim[0] - frame_size <= y <= ylim[1] + frame_size
                ):
                    continue

                txt = self.ax.text(x,
                                   y,
                                   label,
                                   fontsize = self.context.font_size_ring_label,
                                   ha = ha,
                                   va = va,
                                   color = "darkred",
                                   alpha = 0.9,
                                   zorder = 10,
                                   clip_on = True,
                                   path_effects = [
                                       pe.withStroke(linewidth = 1.5, foreground = "white")
                                   ])

                bbox_disp = txt.get_window_extent(renderer = renderer)
                bbox_data = bbox_disp.transformed(self.ax.transData.inverted())
                (x0, y0), (x1, y1) = bbox_data.get_points()

                if (
                    x0 < xlim[0] + margin
                    or x1 > xlim[1] - margin
                    or y0 < ylim[0] + margin
                    or y1 > ylim[1] - margin
                ):
                    txt.remove()

    def _draw_bearing_rays(self, site_x: float, site_y: float) -> None:
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        frame_width = xlim[1] - xlim[0]
        frame_height = ylim[1] - ylim[0]
        frame_size = max(frame_width, frame_height)

        label_inset = 0.025 * frame_size
        cardinal_offset = 0.012 * frame_size

        for bearing_deg in range(0, 360, self.bearing_step_deg):
            theta = np.deg2rad(bearing_deg)

            dx = np.sin(theta)
            dy = np.cos(theta)

            end = self._ray_rectangle_nearest_intersection(site_x, site_y,
                                                           dx, dy,
                                                           xlim, ylim)
            if end is None:
                continue

            end_x, end_y = end

            self.ax.plot([site_x, end_x], [site_y, end_y],
                         linewidth = 0.6, color = "0.3",
                         alpha = 0.4, zorder = 1)

            label_x, label_y, ha, va = (
                self._bearing_label_position_inside_frame(bearing_deg = bearing_deg,
                                                          end_x = end_x, end_y = end_y,
                                                          dx = dx, dy = dy,
                                                          xlim = xlim, ylim = ylim,
                                                          inset = label_inset,
                                                          cardinal_offset = cardinal_offset,
                                                          )
            )

            self.ax.text(label_x,
                         label_y,
                         f"{bearing_deg}°",
                         fontsize = self.context.font_size_bearing_label,
                         ha = ha,
                         va = va,
                         color = "darkred",
                         alpha = 0.9,
                         zorder = 20,
                         clip_on = True,
                         path_effects = [
                             pe.withStroke(linewidth = 1.8, foreground = "white")
                         ])

    @staticmethod
    def _bearing_label_position_inside_frame(bearing_deg: int,
                                             end_x: float, end_y: float,
                                             dx: float, dy: float,
                                             xlim: tuple[float, float], ylim: tuple[float, float],
                                             inset: float, cardinal_offset: float,) -> tuple[float, float, str, str]:
        xmin, xmax = xlim
        ymin, ymax = ylim

        label_x = end_x - inset * dx
        label_y = end_y - inset * dy

        normalized = bearing_deg % 360

        if normalized == 0:
            label_x -= 2.5 * cardinal_offset
        elif normalized == 180:
            label_x += 2.5 * cardinal_offset
        elif normalized == 90:
            label_y += cardinal_offset
        elif normalized == 270:
            label_y -= cardinal_offset

        label_x = min(max(label_x, xmin + inset), xmax - inset)
        label_y = min(max(label_y, ymin + inset), ymax - inset)

        return label_x, label_y, "center", "center"

    @staticmethod
    def _ray_rectangle_nearest_intersection(x0: float, y0: float,
                                            dx: float, dy: float,
                                            xlim: tuple[float, float], ylim: tuple[float, float]) -> tuple[float, float] | None:
        t_candidates = []

        if dx != 0:
            t_candidates.extend(
                [
                    (xlim[0] - x0) / dx,
                    (xlim[1] - x0) / dx,
                ]
            )

        if dy != 0:
            t_candidates.extend(
                [
                    (ylim[0] - y0) / dy,
                    (ylim[1] - y0) / dy,
                ]
            )

        valid_points = []

        for t in t_candidates:
            if t <= 0:
                continue

            x = x0 + t * dx
            y = y0 + t * dy

            if xlim[0] <= x <= xlim[1] and ylim[0] <= y <= ylim[1]:
                valid_points.append((t, x, y))

        if not valid_points:
            return None

        _, x, y = min(valid_points, key = lambda value: value[0])
        return x, y

    def _plot_local_basemap(self, pad_ratio: float = 0.01) -> None:
        if self.context.basemap_path is None:
            raise ValueError("Local basemap overlay requested, but basemap_path is None")

        xmin, ymin, xmax, ymax = self._get_padded_bounds(pad_ratio)
        bbox_geometry = box(xmin, ymin, xmax, ymax)

        bbox_gdf = gpd.GeoDataFrame(geometry = [bbox_geometry],
                                    crs = self.grid_web_mercator.crs)

        basemap = gpd.read_file(self.context.basemap_path).to_crs(epsg = self.epsg)
        clipped = gpd.clip(basemap, bbox_gdf)

        clipped.plot(ax = self.ax,
                     color = "whitesmoke",
                     edgecolor = "lightgray",
                     linewidth = 0.3,
                     zorder = 1)

        clipped.boundary.plot(ax = self.ax,
                              color = "grey",
                              linewidth = 0.8,
                              zorder = 2)

    def _plot_contextily_basemap(self) -> None:
        provider = self.context.basemap_provider.lower()
        crs = self.grid_web_mercator.crs

        if provider == "terrain":
            source = cx.providers.Stadia.StamenTerrainBackground(api_key = self.context.api_key)
            source["url"] = source["url"] + f"?api_key={self.context.api_key}"
            #cx.add_basemap(self.ax, source = cx.providers.Esri.WorldShadedRelief, alpha = 0.55, crs = crs, reset_extent = False)
            cx.add_basemap(self.ax, crs = crs, source = source)
            return

        if provider == "positron":
            cx.add_basemap(self.ax, source = cx.providers.CartoDB.PositronNoLabels, alpha = 0.3, crs = crs, reset_extent = False)
            cx.add_basemap(self.ax, source = cx.providers.CartoDB.PositronOnlyLabels, alpha = 0.6, crs = crs, reset_extent = False)
            return

        raise ValueError(f"Unsupported basemap_provider: {self.context.basemap_provider!r}")

    def _get_padded_bounds(self, pad_ratio: float = 0.05) -> tuple[float, float, float, float]:
        xmin, ymin, xmax, ymax = self.grid_web_mercator.total_bounds

        xpad = (xmax - xmin) * pad_ratio
        ypad = (ymax - ymin) * pad_ratio

        return xmin - xpad, ymin - ypad, xmax + xpad, ymax + ypad

    def apply_map_extent(self) -> None:
        mode = self.result_plot_params.get("extent_mode", "auto")

        if mode == "auto":
            self.crop_to_attached_classes()
            return

        if mode == "fixed-km":
            extent = self.result_plot_params.get("extent_km")
            if extent is None:
                raise ValueError("extent_mode='fixed-km' requires extent_km")
            self._apply_fixed_km_extent()
            return

        if mode == "fixed-lonlat":
            extent = self.result_plot_params.get("extent_lonlat")
            if extent is None:
                print("extent_mode='fixed-lonlat' requires extent_lonlat")
                extent = self.compute_active_lonlat_extent()
                print(f"extent_lonlat set to = {extent}")

            self._apply_fixed_lonlat_extent(extent)
            return

        raise ValueError(f"Unsupported extent_mode: {mode!r}")

    def _apply_fixed_km_extent(self) -> None:
        extent = self.result_plot_params.get("extent_km")

        if extent is None or len(extent) != 4:
            raise ValueError("extent_km must be [xmin_km, xmax_km, ymin_km, ymax_km]")

        xmin_km, xmax_km, ymin_km, ymax_km = map(float, extent)
        site_x, site_y = self._release_site_projected()

        self.ax.set_xlim(site_x + xmin_km * 1000.0, site_x + xmax_km * 1000.0)
        self.ax.set_ylim(site_y + ymin_km * 1000.0, site_y + ymax_km * 1000.0)

    def _apply_fixed_lonlat_extent(self, extent: tuple[float, float, float, float]) -> None:
        if len(extent) != 4:
            raise ValueError("extent_lonlat must be "
                             "[min_lon, min_lat, max_lon, max_lat]")

        min_lon, min_lat, max_lon, max_lat = map(float, extent)

        bbox = (gpd.GeoDataFrame(geometry = [box(min_lon, min_lat, max_lon, max_lat)], crs = "EPSG:4326")
                .to_crs(epsg = self.epsg))

        minx, miny, maxx, maxy = bbox.total_bounds

        self.ax.set_xlim(minx, maxx)
        self.ax.set_ylim(miny, maxy)

    def compute_grid_lonlat_extent(self, padding_ratio: float = 0.02):
        bounds = self.grid_web_mercator.to_crs("EPSG:4326").total_bounds

        min_lon, min_lat, max_lon, max_lat = bounds

        lon_pad = (max_lon - min_lon) * padding_ratio
        lat_pad = (max_lat - min_lat) * padding_ratio

        return (
            min_lon - lon_pad,
            min_lat - lat_pad,
            max_lon + lon_pad,
            max_lat + lat_pad,
        )

    def compute_active_lonlat_extent(self, padding_ratio: float = 0.10):
        active = self.grid_web_mercator[self.grid_web_mercator["grid_class"].notna()]

        if active.empty:
            return self.compute_grid_lonlat_extent(padding_ratio = 0.02)

        min_lon, min_lat, max_lon, max_lat = active.to_crs("EPSG:4326").total_bounds

        lon_pad = (max_lon - min_lon) * padding_ratio
        lat_pad = (max_lat - min_lat) * padding_ratio

        return (
            min_lon - lon_pad,
            min_lat - lat_pad,
            max_lon + lon_pad,
            max_lat + lat_pad,
        )