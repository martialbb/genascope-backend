import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_repositories():
    class MockRepositories:
        def __getattr__(self, name):
            return MagicMock()
    return MockRepositories()
