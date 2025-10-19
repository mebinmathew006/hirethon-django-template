"""
Main test runner for managers app.
This file imports all test modules to ensure they are discovered by pytest.
"""

# Import all test modules to ensure they are discovered
from .tests.test_models import *
from .tests.test_slot_service import *
from .tests.test_views import *
