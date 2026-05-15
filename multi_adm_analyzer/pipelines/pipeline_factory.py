from enum import Enum

from multi_adm_analyzer.config.settings import Settings
from multi_adm_analyzer.domain.overlay_mode import OverlayMode
from multi_adm_analyzer.pipelines.overlay_pipeline import OverlayPipeline
from multi_adm_analyzer.pipelines.probabilistic_pipeline import ProbabilisticPipeline
from multi_adm_analyzer.pipelines.relative_frequency_pipeline import RelativeFrequencyPipeline
from multi_adm_analyzer.pipelines.threshold_overlay_pipeline import ThresholdOverlayPipeline


class PipelineMode(Enum):
    PROBABILISTIC = "probabilistic"
    RELATIVE_FREQUENCY = "relative-frequency"
    OVERLAY = "overlay"
    THRESHOLD_OVERLAY = "threshold-overlay"

    @classmethod
    def parse(cls, value: str) -> "PipelineMode":
        normalized = value.lower().replace("_", "-")

        for mode in cls:
            if mode.value == normalized:
                return mode

        valid = ", ".join(mode.value for mode in cls)
        raise ValueError(f"Unknown pipeline: {value!r}. Expected one of: {valid}")


class PipelineFactory:
    @staticmethod
    def create(settings: Settings, pipeline_name: str, overlay_mode: str = "union"):
        pipeline_mode = PipelineMode.parse(pipeline_name)

        if pipeline_mode is PipelineMode.PROBABILISTIC:
            return ProbabilisticPipeline(settings)

        if pipeline_mode is PipelineMode.RELATIVE_FREQUENCY:
            return RelativeFrequencyPipeline(settings)

        if pipeline_mode is PipelineMode.OVERLAY:
            return OverlayPipeline(settings,
                                   mode = PipelineFactory._parse_overlay_mode(overlay_mode))

        if pipeline_mode is PipelineMode.THRESHOLD_OVERLAY:
            return ThresholdOverlayPipeline(settings,
                                            mode = PipelineFactory._parse_overlay_mode(overlay_mode))

        raise AssertionError(f"Unhandled pipeline mode: {pipeline_mode}")

    @staticmethod
    def _parse_overlay_mode(value: str) -> OverlayMode:
        normalized = value.upper().replace("-", "_")

        try:
            return OverlayMode[normalized]
        except KeyError as exc:
            valid = ", ".join(mode.name.lower() for mode in OverlayMode)
            raise ValueError(f"Unknown overlay mode: {value!r}. Expected one of: {valid}") from exc