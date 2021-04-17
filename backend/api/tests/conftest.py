# This are meant to be heavily mocked unit tests that are fast to run and thus convenient to do so after each save.

import pytest
from api import create_app


@pytest.fixture(scope="module")
def api_client():
    
    app = create_app(debug=False)
    with app.test_client() as client:
        yield client
