import logging
import logging.config
import os
import re
from pathlib import Path
from functools import partial

import yaml

from prefect.utilities.settings import Settings, LoggingSettings
from prefect.utilities.collections import dict_to_flatdict, flatdict_to_dict


# This path will be used if `LoggingSettings.settings_path` does not exist
DEFAULT_LOGGING_SETTINGS_PATH = Path(__file__).parent / "logging.yml"

# Regex call to replace non-alphanumeric characters to '_' to create a valid env var
to_envvar = partial(re.sub, re.compile(r"[^0-9a-zA-Z]+"), "_")


def load_logging_config(path: Path, settings: LoggingSettings) -> dict:
    """
    Loads logging configuration from a path allowing override from the environment
    """
    config = yaml.safe_load(path.read_text())

    # Load overrides from the environment
    env_prefix = settings.Config.env_prefix
    flat_config = dict_to_flatdict(config)
    for key_tup in flat_config.keys():
        override_val = os.environ.get(
            # Generate a valid environment variable with nesting indicated with '_'
            to_envvar((env_prefix + "_".join(key_tup)).upper())
        )
        if override_val:
            flat_config[key_tup] = override_val

    return flatdict_to_dict(flat_config)


def setup_logging(settings: Settings) -> None:

    # If the user has specified a logging path and it exists we will ignore the
    # default entirely rather than dealing with complex merging
    config = load_logging_config(
        (
            settings.logging.settings_path
            if settings.logging.settings_path.exists()
            else DEFAULT_LOGGING_SETTINGS_PATH
        ),
        settings.logging,
    )

    logging.config.dictConfig(config)


def get_logger(name: str = None) -> logging.Logger:
    logger = logging.getLogger("prefect")
    if name:
        logger = logger.getChild(name)
    return logger


class OrionHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        # TODO: Implement a log handler that sends logs to Orion, Core uses a custom
        #       queue to batch messages but we may want to use the stdlib
        #       `MemoryHandler` as a base which implements queueing already
        #       https://docs.python.org/3/howto/logging-cookbook.html#buffering-logging-messages-and-outputting-them-conditionally
        pass


class JsonFormatter(logging.Formatter):
    # TODO: Implement a log formatter that converts `LogRecord` to JSON for Orion
    pass


class RunContextInjector(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # TODO: Inject real information about the run into log records
        record.flow_run_id = "flow-run-id"
        return True
