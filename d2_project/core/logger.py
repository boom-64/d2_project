"""Logger for d2_project."""

# ==== Standard Imports ====
import logging


def get_logger(name: str) -> logging.Logger:
    """Get logger.

    Args:
        name (str): Module/package name.

    Returns:
        logging.Logger: Logger.

    """
    logging.basicConfig(
        filename="app.log",
        filemode="a",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    return logging.getLogger(name)
