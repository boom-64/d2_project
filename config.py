
# ==== Standard Libraries ====

from dataclasses import dataclass, fields
from string import Template
from pathlib import Path
import textwrap
from typing import Any

# ==== Non-Standard Libraries ====

import toml

# ==== Classes ====

@dataclass(frozen=True)
class Settings:

    # ==== Initialised Attributes ====

    _expected_mf_name_template_str: str = "'^${starts_with}[a-fA-F0-9]${extension}$$"
    extension: str = '.content'
    starts_with: str = 'world_sql_content_'

    # ==== Assumed ====

    mf_finder_url: str = 'https://www.bungie.net/Platform/Destiny/Manifest'
    mf_loc_base_url: str = 'https://www.bungie.net'

    # ==== Exposed ====

    mf_lang: str = 'en'
    api_key: str = 'd4705221d56b4040b8c5c6b4ebd58757'
    mf_dir_path: Path = Path('manifest').resolve()
    zip_path: Path = Path('manifest.zip').resolve()
    mf_bak_ext: str = '.bak'

    # ==== Properties ====

    @property
    def expected_mf_name_regex(self) -> str:
        return self.expected_mf_name_template.substitute(
            starts_with=self.starts_with,
            extension=self.extension
        )

    @property
    def expected_mf_name_template(self) -> Template:
        return Template(self._expected_mf_name_template_str)

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

    def _toml_serialise_value(self, value: Any) -> str:
        if isinstance(value, str):
            if self._needs_triple_quotes(value):
                escaped = value.replace('"""', '\\"""')
                return '"""\n' + textwrap.indent(escaped, '    ') + '\n"""'

            else:
                return f'"{value}"'

        elif isinstance(value, bool):
            return "true" if value else "false"

        elif isinstance(value, (int, float)):
            return str(value)

        else:
            return f'"{str(value)}"'

settings: Settings = Settings.from_toml('settings.toml')
settings.regenerate_settings()
