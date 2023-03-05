"""This module contains the standard logging facility.

"""

import logging


logger = logging.getLogger("pybatchintory")
logger.setLevel(logging.DEBUG)

# provide console output
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
logger.addHandler(stream_handler)