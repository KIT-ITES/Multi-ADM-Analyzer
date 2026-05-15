from dataclasses import dataclass
from typing import Mapping

from multi_adm_analyzer.domain.overlay_mode import OverlayMode


@dataclass(frozen = True, slots = True)
class OverlayResult:
    flags_by_cell: dict[int, int]
    counts_by_flag: dict[int, int]


class OverlayClassifier:
    def __init__(self, mode: OverlayMode):
        self.mode = mode

    def classify(self, first_cells: Mapping[int, object],
                 second_cells: Mapping[int, object],
                 third_cells: Mapping[int, object],) -> OverlayResult:

        all_cells = set(first_cells) | set(second_cells) | set(third_cells)

        flags_by_cell: dict[int, int] = {}
        counts_by_flag: dict[int, int] = {}

        for cell in all_cells:
            flag = self._build_flag(cell = cell,
                                    first_cells = first_cells,
                                    second_cells = second_cells,
                                    third_cells = third_cells,
            )

            if self._keep(flag):
                flags_by_cell[int(cell)] = flag
                counts_by_flag[flag] = counts_by_flag.get(flag, 0) + 1

        return OverlayResult(
            flags_by_cell = flags_by_cell,
            counts_by_flag = counts_by_flag,
        )

    def _keep(self, flag: int) -> bool:
        if self.mode is OverlayMode.UNION:
            return True

        if self.mode is OverlayMode.CONSENSUS:
            return flag not in {1, 2, 4}

        if self.mode is OverlayMode.INTERSECTION:
            return flag == 7

        raise ValueError(f"Unsupported overlay mode: {self.mode}")

    @staticmethod
    def _build_flag(cell: int, first_cells: Mapping[int, object],
                    second_cells: Mapping[int, object],
                    third_cells: Mapping[int, object],) -> int:
        flag = 0

        if cell in first_cells:
            flag |= 1

        if cell in second_cells:
            flag |= 2

        if cell in third_cells:
            flag |= 4

        return flag


class OverlayLabelBuilder:
    def build_labels(self, adm1: str, adm2: str, adm3: str,) -> dict[int, str]:
        return {
            1: adm1,
            2: adm2,
            3: f"{adm1}—{adm2}",
            4: adm3,
            5: f"{adm1}—{adm3}",
            6: f"{adm2}—{adm3}",
            7: f"{adm1}—{adm2}—{adm3}",
        }

    def bins_for_mode(self, mode: OverlayMode) -> list[int]:
        if mode is OverlayMode.UNION:
            return [0, 1, 2, 3, 4, 5, 6, 7]

        if mode is OverlayMode.CONSENSUS:
            return [0, 3, 5, 6, 7]

        if mode is OverlayMode.INTERSECTION:
            return [0, 7]

        raise ValueError(f"Unsupported overlay mode: {mode}")