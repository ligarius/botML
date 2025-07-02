import logging
from io import StringIO
from uuid import uuid4
import pytest

@pytest.fixture
def memory_logger():
    stream = StringIO()
    logger = logging.getLogger(f"test_{uuid4()}")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(stream)
    logger.handlers = [handler]
    return logger, stream
