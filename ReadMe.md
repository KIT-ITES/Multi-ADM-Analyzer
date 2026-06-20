# Associated Paper and Data

[![Elsevier](https://a11ybadges.com/badge?logo=elsevier)](https://doi.org/10.1016/j.jenvrad.2026.108075) [![Mendeley](https://a11ybadges.com/badge?logo=mendeley)](https://doi.org/10.17632/kw76hfx5rd.3)

#### Software Heritage Archive

[![SWH](https://archive.softwareheritage.org/badge/swh:1:dir:110974fb0b92149c0b8ac7f2c802a1930752c836/)](https://archive.softwareheritage.org/swh:1:dir:110974fb0b92149c0b8ac7f2c802a1930752c836;origin=https://github.com/KIT-ITES/Multi-ADM-Analyzer;visit=swh:1:snp:40c3c865650f50da99de2b936a1a16a02e32fae3;anchor=swh:1:rev:b69b14d974ff66d2a517da82ae7803e60838893d)


# Multi-ADM-Analyzer

A modular Python framework for post-processing [JRODOS](https://www.ites.kit.edu/english/294.php) atmospheric dispersion model outputs, generating probabilistic exceedance maps, comparing ADMs, and producing publication-quality geospatial visualizations.

The project is designed for:

- ensemble probabilistic dispersion analysis,
- inter-model ADM comparison,
- exceedance-frequency computation,
- multi-model overlay and agreement analysis,
- publication-quality map generation,
- harmonized comparative map panels.

The architecture separates data loading, geospatial processing, statistical computation, plotting, and workflow orchestration.

---

## Features

### Probabilistic Mapping

Generate exceedance probability maps from ensemble simulation outputs.

The probabilistic pipeline:

1. reads all binary result files in a scenario folder,
2. extracts one value per grid cell per file,
3. computes exceedance probability per cell,
4. filters cells by probability threshold,
5. joins results to the computational grid,
6. renders a classified geospatial map.

---

### Relative-Frequency Comparison

Compare two ADMs cell by cell.

For each cell, the relative-frequency pipeline compares how often ADM1 and ADM2 produce non-zero values.

Positive values indicate cells more frequently affected by ADM1. Negative values indicate cells more frequently affected by ADM2.

---

### Overlay Analysis

Compare three ADMs using categorical overlap flags.

The overlay classifier uses bit flags:

```text
1 = ADM1 only
2 = ADM2 only
4 = ADM3 only
3 = ADM1 + ADM2
5 = ADM1 + ADM3
6 = ADM2 + ADM3
7 = ADM1 + ADM2 + ADM3
```

Supported overlay modes:

```text
union
consensus
intersection
```

---

### Threshold Overlay Analysis

The threshold-overlay pipeline first computes exceedance probabilities for each ADM, then overlays only cells whose exceedance probability passes the configured threshold.

This is useful for identifying robust regions of probabilistic agreement across multiple ADMs.

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Multi-Ensemble-Tool
```

---

### 2. Create a Virtual Environment

#### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

#### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Typical geospatial dependencies include:

- numpy
- pandas
- geopandas
- shapely
- matplotlib
- contextily
- rasterio
- pyproj

---

## Project Structure

Recommended refactored structure:

```text
Multi-Ensemble-Tool/
├─ main.py
├─ config.json
├─ requirements.txt
├─ basemaps/
├─ Sites/
└─ multi_ensemble_tool/
   ├─ __init__.py
   ├─ cli.py
   ├─ config/
   │  ├─ __init__.py
   │  ├─ path_resolver.py
   │  └─ settings.py
   ├─ data_io/
   │  ├─ __init__.py
   │  ├─ binary_reader.py
   │  ├─ cell_value_loader.py
   │  ├─ json_writer.py
   │  └─ scenario_discovery.py
   ├─ domain/
   │  ├─ __init__.py
   │  ├─ models.py
   │  └─ overlay_mode.py
   ├─ geo/
   │  ├─ __init__.py
   │  ├─ grid_joiner.py
   │  └─ grid_loader.py
   ├─ pipelines/
   │  ├─ __init__.py
   │  ├─ base_overlay_pipeline.py
   │  ├─ overlay_pipeline.py
   │  ├─ pipeline_factory.py
   │  ├─ probabilistic_pipeline.py
   │  ├─ relative_frequency_pipeline.py
   │  └─ threshold_overlay_pipeline.py
   ├─ plotting/
   │  ├─ __init__.py
   │  ├─ discrete_visualizer.py
   │  ├─ plot_context.py
   │  └─ visualizer.py
   └─ stats/
      ├─ __init__.py
      ├─ common.py
      ├─ exceedance.py
      ├─ frequency.py
      ├─ highlighting.py
      ├─ overlay.py
      └─ statistics_writer.py
```

---

## Internal Architecture

| Module      | Responsibility                                        |
|-------------|-------------------------------------------------------|
| `config`    | Configuration loading and path resolution             |
| `data_io`   | Binary reading, scenario discovery, JSON/debug output |
| `domain`    | Shared domain models and enums                        |
| `geo`       | Grid loading and joining computed values to geometry  |
| `stats`     | Pure statistical computation                          |
| `plotting`  | Matplotlib/GeoPandas map rendering                    |
| `pipelines` | End-to-end workflow orchestration                     |
| `cli.py`    | Command-line argument parsing and pipeline dispatch   |

The main conceptual workflow is:

```text
config.json
   ↓
Settings + PathResolver
   ↓
ScenarioDiscovery
   ↓
CellValueLoader
   ↓
Statistical calculator
   ↓
GridJoiner
   ↓
DiscreteVisualizer
   ↓
PNG/PDF outputs
```

---

## Usage

General command syntax:

```bash
python main.py <pipeline> [options]
```

---

## Available Pipelines

| Pipeline             | Description                                                     |
|----------------------|-----------------------------------------------------------------|
| `probabilistic`      | Generate exceedance probability maps                            |
| `relative-frequency` | Compare two ADMs using signed relative-frequency differences    |
| `overlay`            | Generate categorical three-ADM overlay maps                     |
| `threshold-overlay`  | Generate overlay maps after exceedance probability thresholding |

---

## CLI Examples

### Probabilistic Mapping

```bash
python main.py probabilistic
```

---

### Relative-Frequency ADM Comparison

```bash
python main.py relative-frequency
```

---

### Three-ADM Overlay

```bash
python main.py overlay --overlay-mode intersection
```

Available overlay modes:

```text
union
consensus
intersection
```

---

### Thresholded Overlay

```bash
python main.py threshold-overlay --overlay-mode consensus
```

---

### Use a Custom Config File

```bash
python main.py probabilistic --config configs/borssele.json
```

---

## Use Cases

### 1. Ensemble Exceedance Analysis

Use:

```bash
python main.py probabilistic
```

Typical outputs:

- exceedance probability maps,
- maximum-probability cell highlighting,
- probability statistics,
- cell-value debug logs.

---

### 2. ADM Pairwise Comparison

Use:

```bash
python main.py relative-frequency
```

Useful for:

- comparing ADM spatial footprints,
- finding areas where one ADM is more frequently active,
- supporting inter-model sensitivity analysis.

---

### 3. Multi-ADM Agreement Analysis

Use:

```bash
python main.py overlay --overlay-mode intersection
```

Useful for:

- finding cells affected by all ADMs,
- identifying consensus spatial regions,
- supporting robust plume/agreement interpretation.

---

### 4. Thresholded Probabilistic Agreement

Use:

```bash
python main.py threshold-overlay --overlay-mode consensus
```

Useful for:

- filtering low-probability cells,
- comparing high-confidence exceedance regions,
- emergency-planning or conservative risk-map workflows.

---

## Input Data Format

Each binary result file is expected to contain:

```text
8-byte header:
  rows: big-endian int32
  cols: big-endian int32

then:
  rows * cols float32 values, big-endian
```

The reader reshapes the matrix and extracts the last column:

```text
cell_id -> scalar value
```

Across all files in one scenario folder, the loader builds:

```python
dict[int, list[float]]
```

Example:

```python
{
    10: [0.0, 1.2, 0.4, ...],
    11: [0.0, 0.0, 2.1, ...],
}
```

---

## Configuration File

The project is configuration-driven. Most scientific and plotting choices can be changed without modifying the source code.

Default file:

```text
config.json
```

---

## Configuration Template

```json
{
  "year": "2024",

  "ADM1": "RIMPUFF",
  "ADM2": "DIPCOT",
  "ADM3": "LASAT",

  "site_name": "Borssele",
  "site_coord": "3.7187, 51.4311",
  
  "analysis_epsg": 32631,
  
  "root_1": "C:\\Users\\USER\\Data\\SITE\\ADM\\2024_1",
  "root_2": "C:\\Users\\USER\\Data\\SITE\\ADM\\2024_1",
  "root_3": "C:\\Users\\USER\\Data\\SITE\\ADM\\2024_1",

  "relative_adms": "C:\\Users\\USER\\Data\\SITE\\Relative_Frequency\\ADM1_ADM2",
  "overlay_adms": "C:\\Users\\USER\\Data\\SITE\\Overlay_ADMS\\ADM1_ADM2_ADM3",

  "log_path": "C:\\Users\\USER\\Data\\SITE",
  "write_debug_logs": false,
  "grid_path": "C:\\Users\\USER\\Data\\JRodos_Computational_Grid\\SITE",

  "exceed_level": 1.0,
  "exceed_unit": "",
  "threshold": 0.0,

  "basemap_path": "basemaps/europe.shp",
  "with_local_basemap_overlay": true,

  "plot_settings": {
    "figure_size": [12, 10],
    "dpi": 600,

    "font_size_title": 16,
    "font_size_axis_label": 13,
    "font_size_tick_label": 12,
    "font_size_ring_label": 11,
    "font_size_bearing_label": 11,
    "font_size_legend": 11,
    "font_size_legend_title": 12,

    "show_legend": false,
    "export_legend": false,
    "legend_frame": true,

    "basemap_provider": "terrain"
  },

  "visual_parameters": {
    "evacuation": {
      "major_step_km": 50,
      "minor_step_km": 25,
      "ring_step_km": 25,
      "max_radius_km": 400,
      "show_bearings": true,
      "bearing_step_deg": 45,
      "padding_km": 10,

      "extent_mode": "auto",
      "extent_km": [-100, 100, -125, 100],
      "extent_lonlat": [2.2, 50.3, 5.12, 52.4]
    },

    "sheltering": {
      "major_step_km": 100,
      "minor_step_km": 50,
      "ring_step_km": 50,
      "max_radius_km": 400,
      "show_bearings": true,
      "bearing_step_deg": 45,
      "padding_km": 15,

      "extent_mode": "auto",
      "extent_km": [-200, 200, -200, 200],
      "extent_lonlat": [3.0, 50.0, 9.0, 55.0]
    }
  },

  "RIMPUFF": {
    "probabilistic_plots_params": {
      "Borssele": {
        "box_anchors": {
          "evacuation": [0.03, 0.95],
          "sheltering": [0.80, 0.99]
        }
      }
    }
  },

  "RIMPUFF-DIPCOT": {
    "difference_plots_params": {
      "Borssele": {
        "box_anchors": {
          "evacuation": [0.10, 0.40],
          "sheltering": [0.82, 0.95]
        }
      }
    }
  },

  "RIMPUFF-DIPCOT-LASAT": {
    "union_plots_params": {
      "Borssele": {
        "box_anchors": {
          "evacuation": [0.03, 0.35],
          "sheltering": [0.01, 0.95]
        }
      }
    },
    "consensus_plots_params": {
      "Borssele": {
        "box_anchors": {
          "evacuation": [0.03, 0.35],
          "sheltering": [0.01, 0.95]
        }
      }
    },
    "intersection_plots_params": {
      "Borssele": {
        "box_anchors": {
          "evacuation": [0.03, 0.35],
          "sheltering": [0.01, 0.95]
        }
      }
    }
  }
}
```

---

## Configuration Key Explanation

### `year`

```json
"year": "2024"
```

Used in output directory naming.

---

### `ADM1`, `ADM2`, `ADM3`

```json
"ADM1": "RIMPUFF"
```

ADM names used for:

- path token replacement,
- output naming,
- plot titles,
- legends,
- overlay labels.

---

### `site_name`

```json
"site_name": "Borssele"
```

Human-readable site identifier.

Used for:

- path token replacement,
- plot titles,
- legend labels,
- lookup of site-specific legend anchors.

---

### `site_coord`

```json
"site_coord": "3.7187, 51.4311"
```

Release-site coordinate.

Format:

```text
longitude, latitude
```

Coordinate system:

```text
EPSG:4326
```

---

### `analysis_epsg`

```json
"analysis_epsg": 32631
```

Projected metric CRS used by the visualizer.

Used for:

- converting the grid before plotting,
- release-site projection,
- distance axes in kilometres,
- polar distance rings,
- bearing rays,
- local vector basemap reprojection.

Choose a CRS appropriate for the site. For example:

| Region | Possible CRS |
|---|---|
| Western Europe / UTM zone 31N | EPSG:32631 |
| Central Europe / UTM zone 32N | EPSG:32632 |
| Eastern Central Europe / UTM zone 33N | EPSG:32633 |
| Europe-wide metric analysis | EPSG:3035 |

---

### `root_1`, `root_2`, `root_3`

```json
"root_1": "C:\\Users\\USER\\Data\\SITE\\ADM\\2024_1"
```

Root directories for ADM scenario folders.

Each root should contain scenario subfolders:

```text
2024_1/
  Evacuation/
  Sheltering/
```

Each scenario folder contains binary ensemble files.

---

## Supported Path Styles

The path resolver supports both direct paths and tokenized template paths.

### 1. Explicit Direct Paths

Example:

```json
"root_1": "Sites/Borssele/RIMPUFF"
```

This is used exactly as written.

It may be:

- project-relative,
- absolute.

Example absolute path:

```json
"root_1": "C:\\Data\\Borssele\\RIMPUFF"
```

---

### 2. Tokenized Template Paths

Example:

```json
"root_1": "C:\\Users\\USER\\Data\\SITE\\ADM\\2024_1"
```

Supported complete path-segment tokens:

| Token | Replaced with |
|---|---|
| `USER` | Current system username |
| `SITE` | `site_name` |
| `ADM` | Current ADM name |

For example, with:

```json
"site_name": "Borssele",
"ADM1": "RIMPUFF"
```

this:

```json
"root_1": "C:\\Users\\USER\\Data\\SITE\\ADM\\2024_1"
```

resolves to:

```text
C:\Users\<current-user>\Data\Borssele\RIMPUFF\2024_1
```

Token replacement only occurs for complete path segments. A normal path such as:

```json
"root_1": "Sites/Borssele/RIMPUFF"
```

does not require or trigger replacement.

---

### `relative_adms`

```json
"relative_adms": "C:\\Users\\USER\\Data\\SITE\\Relative_Frequency\\ADM1_ADM2"
```

Output directory template for relative-frequency maps.

Supports named replacement tokens:

| Token | Meaning |
|---|---|
| `USER` | Current system username |
| `SITE` | Current site name |
| `ADM1` | First ADM |
| `ADM2` | Second ADM |

---

### `overlay_adms`

```json
"overlay_adms": "C:\\Users\\USER\\Data\\SITE\\Overlay_ADMS\\ADM1_ADM2_ADM3"
```

Output directory template for overlay and threshold-overlay maps.

Supports:

| Token | Meaning |
|---|---|
| `USER` | Current system username |
| `SITE` | Current site name |
| `ADM1` | First ADM |
| `ADM2` | Second ADM |
| `ADM3` | Third ADM |

---

### `log_path`

```json
"log_path": "C:\\Users\\USER\\Data\\SITE"
```

General log/output root path. Some pipeline-specific outputs are written to generated output directories instead.

---

### `write_debug_logs`

```json
"write_debug_logs": false
```

Enable/disabe dumping the parsed and generated data to log files

---

### `grid_path`

```json
"grid_path": "C:\\Users\\USER\\Data\\JRodos_Computational_Grid\\SITE"
```

Path to the computational grid.

Requirements:

- readable by GeoPandas,
- has a geometry column,
- has a CRS,
- contains either a `Cell` or `cell_id` column.

The grid is loaded by `GridLoader` and joined with computed cell values through `GridJoiner`.

---

### `exceed_level`

```json
"exceed_level": 1.0
```

Value used to compute exceedance probabilities.

For each cell:

```text
probability = number of runs where value >= exceed_level / total number of runs
```

---

### `exceed_unit`

```json
"exceed_unit": ""
```

Display unit for scientific interpretation.

Examples:

```json
"exceed_unit": "mSv"
```

or:

```json
"exceed_unit": "Bq/m²"
```

---

### `threshold`

```json
"threshold": 0.1
```

Probability threshold.

For example:

```text
0.1 = 10%
```

Cells with probabilities less than or equal to this threshold are excluded from probability maps and threshold-overlay presence maps.

---

### `basemap_path`

```json
"basemap_path": "basemaps/europe.shp"
```

Path to local vector basemap.

Used when:

```json
"with_local_basemap_overlay": true
```

---

### `with_local_basemap_overlay`

```json
"with_local_basemap_overlay": true
```

Controls basemap mode.

#### `true`

Uses the local vector basemap from `basemap_path`.

This is stable and does not require internet access.

#### `false`

Uses an online contextily basemap.

This requires internet access and compatible geospatial dependencies.

---

## Plot Settings

### `figure_size`

```json
"figure_size": [12, 10]
```

Matplotlib figure size in inches.

Use the same value across comparable maps for publication panels.

---

### `dpi`

```json
"dpi": 600
```

Raster export resolution for PNG output.

---

### Typography Settings

```json
"font_size_title": 16,
"font_size_axis_label": 13,
"font_size_tick_label": 12,
"font_size_ring_label": 11,
"font_size_bearing_label": 11,
"font_size_legend": 11,
"font_size_legend_title": 12
```

Controls plot title, axis labels, tick labels, ring labels, bearing labels, and legend text.

---

### `show_legend`

```json
"show_legend": false
```

Controls whether the legend is drawn inside the map.

---

### `export_legend`

```json
"export_legend": true
```

Exports the legend as a standalone figure.

Recommended for publication panels where one shared legend is used for multiple maps.

---

### `legend_frame`

```json
"legend_frame": true
```

Controls whether the legend has a surrounding box.

---

### `basemap_provider`

```json
"basemap_provider": "terrain"
```

Used only when:

```json
"with_local_basemap_overlay": false
```

Supported values:

```text
terrain
positron
```

#### `terrain`

Uses Esri World Terrain.

Useful when topographic context is scientifically relevant.

#### `positron`

Uses CartoDB Positron.

Useful for clean, low-contrast publication maps.

---

## Visual Parameters

Visual parameters are defined per scenario.

Example:

```json
"visual_parameters": {
  "evacuation": {
    "major_step_km": 50,
    "minor_step_km": 25,
    "ring_step_km": 25,
    "max_radius_km": 400,
    "show_bearings": true,
    "bearing_step_deg": 45,
    "padding_km": 10,
    "extent_mode": "auto"
  }
}
```

Scenario keys must match folder names case-insensitively, because the visualizer uses `scenario_name.lower()`.

---

### `major_step_km`

Major tick interval for distance axes.

---

### `minor_step_km`

Minor tick interval for distance axes.

---

### `ring_step_km`

Spacing between polar distance rings.

---

### `max_radius_km`

Maximum radius for polar reference rings.

---

### `show_bearings`

Controls whether bearing rays are drawn.

---

### `bearing_step_deg`

Angular spacing between bearing rays.

Example:

```json
"bearing_step_deg": 45
```

draws rays at:

```text
0°, 45°, 90°, 135°, ...
```

---

### `padding_km`

Padding added around active cells when using automatic extent mode.

---

## Extent Modes

### `auto`

```json
"extent_mode": "auto"
```

Automatically crops the map to active classified cells.

Useful for quick exploratory plots.

---

### `fixed-km`

```json
"extent_mode": "fixed-km",
"extent_km": [-100, 100, -125, 100]
```

Uses fixed map bounds in kilometres relative to the release site.

Format:

```text
[xmin_km, xmax_km, ymin_km, ymax_km]
```

This is useful when comparing maps from the same site and wanting a consistent metric window around the release point.

---

### `fixed-lonlat`

```json
"extent_mode": "fixed-lonlat",
"extent_lonlat": [2.2, 50.3, 5.12, 52.4]
```

Uses fixed geographic bounds.

Format:

```text
[min_lon, min_lat, max_lon, max_lat]
```

Recommended for publication panels when reviewers request identical latitude/longitude ranges across comparable ADM maps.

If `extent_mode` is `fixed-lonlat` and `extent_lonlat` is omitted, the current plotting logic may compute an active-cell geographic extent as fallback, depending on implementation.

---

## ADM-Specific Plot Anchors

The config can define legend positions per ADM combination and scenario.

Example for a probabilistic map:

```json
"RIMPUFF": {
  "probabilistic_plots_params": {
    "Borssele": {
      "box_anchors": {
        "evacuation": [0.03, 0.95],
        "sheltering": [0.80, 0.99]
      }
    }
  }
}
```

Example for relative-frequency maps:

```json
"RIMPUFF-DIPCOT": {
  "difference_plots_params": {
    "Borssele": {
      "box_anchors": {
        "evacuation": [0.10, 0.40],
        "sheltering": [0.82, 0.95]
      }
    }
  }
}
```

Example for overlay maps:

```json
"RIMPUFF-DIPCOT-LASAT": {
  "intersection_plots_params": {
    "Borssele": {
      "box_anchors": {
        "evacuation": [0.03, 0.35],
        "sheltering": [0.01, 0.95]
      }
    }
  }
}
```

These values are passed to Matplotlib as `bbox_to_anchor`.

---

## Outputs

Depending on the selected pipeline, outputs may include:

- PNG maps,
- PDF maps,
- standalone legend files,
- statistical summaries,
- raw cell-value JSON logs,
- exceedance probability JSON logs,
- relative-frequency difference JSON logs,
- overlay classification JSON logs.

---

## Example Workflow

For side-by-side ADM comparison panels:

```json
"figure_size": [12, 10],
"show_legend": false,
"export_legend": true
```

For harmonized geographic panels:

```json
"extent_mode": "fixed-lonlat",
"extent_lonlat": [2.2, 50.3, 5.12, 52.4]
```

For harmonized metric panels around the source:

```json
"extent_mode": "fixed-km",
"extent_km": [-100, 100, -125, 100]
```

For terrain context:

```json
"with_local_basemap_overlay": false,
"basemap_provider": "terrain"
```

For reproducible offline plotting:

```json
"with_local_basemap_overlay": true,
"basemap_path": "basemaps/europe.shp"
```

---