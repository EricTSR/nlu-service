from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.main import create_application


@pytest.fixture
def client() -> Iterator[TestClient]:
    application = create_application()
    with TestClient(application) as test_client:
        yield test_client
