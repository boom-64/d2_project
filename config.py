
# ==== Standard Libraries ====

from dataclasses import dataclass, fields
from string import Template
from pathlib import Path
import textwrap
from types import MappingProxyType
from typing import Any
import re

# ==== Non-Standard Libraries ====

import toml

# ==== Classes ====

@dataclass(frozen=True)
class Settings:

    # ==== Manifest Filename Attributes ====

    _expected_mf_name_template_str: str = '^${starts_with}[a-fA-F0-9]{32}${extension}$$'
    extension: str = '.content'
    starts_with: str = 'world_sql_content_'
    mf_zip_structure: MappingProxyType = MappingProxyType({
        'expected_dir_count': 0,
        'expected_file_count': 1
    })

    # ==== Bungie Request Attributes ====

    mf_finder_url: str = 'https://www.bungie.net/Platform/Destiny/Manifest'
    mf_loc_base_url: str = 'https://www.bungie.net'
    mf_lang: str = 'en'
    api_key: str = 'd4705221d56b4040b8c5c6b4ebd58757'
    force_update: bool = True

    # ==== Local Filesystem Attributes ====

    mf_dir_path: Path = Path('manifest').resolve()
    mf_bak_ext: str = '.bak'

    # ==== Properties ====

    @property
    def expected_mf_name_template(self) -> Template:
        return Template(self._expected_mf_name_template_str)

    @property
    def expected_mf_name_regex(self) -> str:
        return self.expected_mf_name_template.substitute(
            starts_with=self.starts_with,
            extension=self.extension
        )

    # ==== Class Methods ====

    @classmethod
    def from_toml(cls, filepath):
        data = toml.load(filepath)
        return cls(**data)

    # ==== Public Methods ====

    def regenerate_settings(self):
        with open('settings.toml', 'w') as toml_open:
            for field in fields(self):
                name = field.name
                default = field.default

                serialised_lines = self._toml_serialise_value(
                    default
                ).splitlines()

                toml_open.write(f"# {name} = {serialised_lines[0]}\n")
                for line in serialised_lines[1:]:
                    toml_open.write(f"# {line}\n")

    # ==== Private Methods ====

    def _needs_triple_quotes(self, s: str) -> bool:
        special_chars = ['\n', '\r', '"', "'"]

        return any(c in s for c in special_chars)

    def _is_bare_key(self, s: str) -> bool:
        return re.fullmatch(r'[A-Za-z0-9_-]+', s) is not None

    def _toml_serialise_value(self, value: Any) -> str:
        if isinstance(value, str):
            if self._needs_triple_quotes(value):
                escaped = value.replace('"""', '\\"""')
                return '"""\n' + textwrap.indent(escaped, '    ') + '\n"""'

            else:
                return f'"{value}"'

        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, Path):
            return f'"{value}"'
        elif isinstance(value, (int, float)):
            return str(value)

        elif isinstance(value, MappingProxyType):
            if not value:
                return "{ }"

            parts = []

            for key, val in value.items():
                bare_key = key
                if not self._is_bare_key(key):
                    bare_key = f'"{key}"'

                parts.append(f'{bare_key} = {self._toml_serialise_value(val)}')

            return "{ " + ", ".join(parts) + " }"

        else:
            raise TypeError(f"Unsupported TOML type: {type(value)}")

settings: Settings = Settings.from_toml('settings.toml')
settings.regenerate_settings()
