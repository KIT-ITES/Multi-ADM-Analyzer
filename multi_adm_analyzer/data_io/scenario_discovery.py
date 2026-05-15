from pathlib import Path
from typing import Iterable

from multi_adm_analyzer.domain.models import AdmPaths, Scenario


class ScenarioDiscovery:
    """finds valid scenarios"""
    def discover_single_adm(self, adm: AdmPaths) -> list[Scenario]:
        scenarios: list[Scenario] = []

        for path in sorted(adm.root.iterdir()):
            if not self._is_valid_scenario_dir(path):
                continue

            scenarios.append(Scenario(name = path.name,
                                      paths_by_adm = {adm.adm_name: path})
                             )

        return scenarios

    def discover_common_scenarios(self, adms: Iterable[AdmPaths]) -> list[Scenario]:
        adm_list = list(adms)

        if not adm_list:
            return []

        scenario_names_by_adm = {
            adm.adm_name: self._scenario_names(adm.root)
            for adm in adm_list
        }

        common_names = set.intersection(*scenario_names_by_adm.values())

        scenarios: list[Scenario] = []

        for scenario_name in sorted(common_names):
            scenarios.append(
                Scenario(
                    name = scenario_name,
                    paths_by_adm = {
                        adm.adm_name: adm.root / scenario_name
                        for adm in adm_list
                    },
                )
            )

        return scenarios

    def report_missing_scenarios(self, adms: Iterable[AdmPaths]) -> dict[str, set[str]]:
        adm_list = list(adms)

        if not adm_list:
            return {}

        scenario_names_by_adm = {
            adm.adm_name: self._scenario_names(adm.root)
            for adm in adm_list
        }

        all_names = set.union(*scenario_names_by_adm.values())

        return {
            adm_name: all_names - scenario_names
            for adm_name, scenario_names in scenario_names_by_adm.items()
        }

    @staticmethod
    def count_files(path: Path) -> int:
        if not path.exists() or not path.is_dir():
            return 0

        return sum(1 for child in path.iterdir() if child.is_file())

    @staticmethod
    def _scenario_names(root: Path) -> set[str]:
        if not root.exists():
            raise FileNotFoundError(f"Scenario root does not exist: {root}")

        return {
            path.name
            for path in root.iterdir()
            if ScenarioDiscovery._is_valid_scenario_dir(path)
        }

    @staticmethod
    def _is_valid_scenario_dir(path: Path) -> bool:
        return path.is_dir() and path.name.lower() != "xmls"