import pytest
from unittest.mock import patch, MagicMock

# Apply patch for MongoDB client at module level
# This will be applied before any test modules are loaded
@pytest.fixture(autouse=True, scope="session")
def patch_mongo_client():
    with patch('app.utils.helper.mongo_client', return_value=MagicMock()):
        yield