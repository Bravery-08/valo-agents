import logging
import sys
from typing import Optional

from .config import get_settings


def configure_logging(level: Optional[int] = None) -> None:
    settings = get_settings()
    log_level = level if level is not None else (logging.DEBUG if settings.debug else logging.INFO)

    # Clear existing handlers to avoid duplicate logs in reloaders
    for handler in list(logging.root.handlers):
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
