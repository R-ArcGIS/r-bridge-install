import logging
import os

LOGGING = False

if LOGGING:
    filename = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "rtools.log")
    logging.basicConfig(filename=filename, level=logging.DEBUG)
    log = logging.getLogger(__name__)
