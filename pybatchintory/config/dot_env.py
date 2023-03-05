from pathlib import Path
from typing import Dict
from copy import copy

from pybatchintory.config import Settings


def instantiate_from_dot_env(env_file: str, settings: Dict) -> Settings:
    """Instantiate settings from configuration file `env_file` while explicitly
    checking that the file exists.

    """

    config_file = Path(env_file)

    if not config_file.exists():
        raise ValueError(f"Path to dot-env file '{env_file}' does not exist.")

    settings = copy(settings)
    settings["ENV_FILE"] = str(env_file)
    return Settings(_env_file=env_file, **settings)
