import pytest
from app.clients.amdalnet_client import AmdalnetClient
from app.data.mock_permits import mock_permits

@pytest.fixture(autouse=True)
def mock_amdalnet_client(monkeypatch):
    """
    Mocks the AmdalnetClient to prevent real HTTP requests during testing.
    This fixture replaces the 'get_sk_final' method with a function
    that returns the static mock_permits data.
    """
    # The lambda function signature must match the original method, including default parameters.
    monkeypatch.setattr(AmdalnetClient, "get_sk_final", lambda self, page=1, limit=100: mock_permits)
