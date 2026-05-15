import argparse
import time
from pathlib import Path
from multi_adm_analyzer.config.settings import Settings
from multi_adm_analyzer.pipelines.pipeline_factory import PipelineFactory


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog = "multi-ensemble-tool",
                                     description = ("Generate probabilistic, relative-frequency, "
                                                    "and overlay ADM maps.")
                                     )

    parser.add_argument("pipeline",
                        default = "probabilistic",
                        choices=[
                            "probabilistic",
                            "relative-frequency",
                            "overlay",
                            "threshold-overlay",
                        ],
                        help = "Pipeline to run.")

    parser.add_argument("--config",
                        default = str(PROJECT_ROOT / "config.json"),
                        help = "Path to config.json.")

    parser.add_argument("--overlay-mode",
                        default = "intersection",
                        choices = [
                            "union",
                            "consensus",
                            "intersection",
                        ],
                        help = "Overlay mode used by overlay pipelines.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    start = time.time()

    settings = Settings.from_file(args.config)

    pipeline = PipelineFactory.create(settings = settings,
                                      pipeline_name = args.pipeline,
                                      overlay_mode = args.overlay_mode)
    pipeline.run()

    print(f"[run] All scenarios finished in {time.time() - start:.2f}s")