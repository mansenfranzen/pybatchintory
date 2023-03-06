import os
from typing import Optional, Dict

from pybatchintory import config
from pybatchintory.config import Settings
from pybatchintory.config.dot_env import instantiate_from_dot_env
from pybatchintory.logging import logger
from pybatchintory import sql

ENV_NAME_CONFIG_FILE = "PYBATCHINTORY_ENV_FILE"


def configure(dot_env: Optional[str] = None,
              settings: Optional[Dict] = None):
    """Globally configure package wide settings which overwrites default
    settings of `pybatchintory.config.values`.

    Configuration settings are evaluated in the following precedence:

    1. Values passed as `settings` parameter to `configure` function.
    2. Specific values provided via environment variables with correct
       naming schema. For example, `BACKEND_CONN` can be specified via the
       environment variable `PYBATCHINVENTORY_BACKEND_CONN`.
    3. Values extracted from a given `dot_env` file via `configure` function.
    4. Values parsed from dot-env file that is specified via the
       `PYBATCHINTORY_ENV_FILE` environment variable.
    5. Default values being specified in the settings source class.

    Parameters
    ----------
    dot_env: str, optional
        Path to dotenv-file which contains the configuration properties.
    settings: dict, optional
        Custom settings which take highest priority over all other sources.

    """

    settings = settings or {}
    var_env_file = os.environ.get(ENV_NAME_CONFIG_FILE)

    if dot_env:
        logger.info(f"Instantiate settings from env file '{dot_env}'.")
        values = instantiate_from_dot_env(dot_env, settings)

    elif var_env_file:
        logger.info(
            f"Instantiate settings from environmental variable "
            f"'{ENV_NAME_CONFIG_FILE}'."
        )
        values = instantiate_from_dot_env(var_env_file, settings)

    elif settings is not None:
        values = Settings(**settings)

    else:
        values = Settings()

    config.settings = values
    sql.db = sql.initialize()
