from typing import Mapping


class SingleRunHighlighter:
    def extract_matching_single_run_cells(self, first_single_run_by_cell: Mapping[int, int],
                                          second_single_run_by_cell: Mapping[int, int],
                                          third_single_run_by_cell: Mapping[int, int],
                                          candidate_cells: set[int],) -> dict[int, int]:
        result: dict[int, int] = {}

        for cell in candidate_cells:
            values: list[int] = []

            if cell in first_single_run_by_cell:
                values.append(first_single_run_by_cell[cell])

            if cell in second_single_run_by_cell:
                values.append(second_single_run_by_cell[cell])

            if cell in third_single_run_by_cell:
                values.append(third_single_run_by_cell[cell])

            if values and len(set(values)) == 1:
                result[int(cell)] = values[0]

        return result