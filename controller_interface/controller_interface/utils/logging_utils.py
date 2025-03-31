# controller_interface/src/utils/logging_utils.py

import logging
import sys

# Create a logger for your package. You can rename "controller_interface" to match your top-level package name.
logger = logging.getLogger("controller_interface")

# Set the base logging level here (DEBUG, INFO, WARNING, etc.)
logger.setLevel(logging.DEBUG)

# Create a console handler to output logs to stdout
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

# Format logs with time, module name, level, and message
formatter = logging.Formatter(
    fmt="[%(asctime)s] %(name)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler.setFormatter(formatter)

# Attach the handler to your logger
logger.addHandler(console_handler)

# Example usage in other files:
# from controller_interface.utils.logging_utils import logger
# logger.debug("Debug message.")
# logger.info("Info-level message.")
# logger.error("Error message.")
