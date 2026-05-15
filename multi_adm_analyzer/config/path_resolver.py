import getpass
import re
from pathlib import Path
from typing import Mapping


class PathResolver:
    """handles ADM/SITE/USER substitutions"""

    _TOKEN_PATTERN = re.compile(r"(?<=[\\/])(ADM|SITE|USER)(?=[\\/])")

    def __init__(self, site_name: str, user: str | None = None):
        self.site_name = site_name
        self.user = user or getpass.getuser()

    def resolve_adm_path(self, template: str, adm_name: str) -> Path:
        mapping = {
            "ADM": adm_name,
            "SITE": self.site_name,
            "USER": self.user,
        }

        resolved = self._TOKEN_PATTERN.sub(
            lambda match: mapping[match.group(1)],
            template,
        )

        return Path(resolved)

    def resolve_named_path(self, template: str, replacements: Mapping[str, str]) -> Path:
        resolved = template.replace("USER", self.user).replace("SITE", self.site_name)

        for key, value in replacements.items():
            resolved = resolved.replace(key, value)

        return Path(resolved)