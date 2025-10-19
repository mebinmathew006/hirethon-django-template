# Unit Testing with Pytest

This project is configured to use pytest for unit testing. The test setup includes Django integration with pytest-django.

## Test Structure

The managers app has a comprehensive test suite located in `hirethon_template/managers/tests/`:

```
managers/tests/
├── __init__.py
├── factories.py          # Factory classes for test data creation
├── test_models.py        # Model unit tests
├── test_slot_service.py  # SlotScheduler service tests
├── test_simple.py        # Simple demonstration tests
└── test_views.py         # API view tests
```

## Running Tests

### Run All Tests
```bash
docker-compose -f local.yml exec django python -m pytest hirethon_template/managers/tests/
```

### Run Specific Test File
```bash
docker-compose -f local.yml exec django python -m pytest hirethon_template/managers/tests/test_models.py
```

### Run Specific Test Class
```bash
docker-compose -f local.yml exec django python -m pytest hirethon_template/managers/tests/test_models.py::TestTeamModel
```

### Run Specific Test Method
```bash
docker-compose -f local.yml exec django python -m pytest hirethon_template/managers/tests/test_models.py::TestTeamModel::test_team_creation
```

### Run Tests with Verbose Output
```bash
docker-compose -f local.yml exec django python -m pytest hirethon_template/managers/tests/ -v
```

### Run Tests and Stop on First Failure
```bash
docker-compose -f local.yml exec django python -m pytest hirethon_template/managers/tests/ -x
```

## Test Configuration

The pytest configuration is defined in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
minversion = "6.0"
addopts = "--ds=config.settings.test --reuse-db"
python_files = [
    "tests.py",
    "test_*.py",
]
```

## Test Database

Tests use the test database configured in `config/settings/test.py`. The `--reuse-db` flag helps speed up test runs by reusing the database between test runs.

## Factory Classes

The test factories are located in `managers/tests/factories.py` and provide easy creation of test objects:

- `TeamFactory` - Creates Team instances
- `TeamMemberFactory` - Creates TeamMember instances  
- `SlotFactory` - Creates Slot instances
- `UserFactory` - Creates User instances (from users app)
- `AvailabilityFactory` - Creates Availability instances
- `HolidayFactory` - Creates Holiday instances
- `LeaveRequestFactory` - Creates LeaveRequest instances
- `SwapRequestFactory` - Creates SwapRequest instances
- `AlertFactory` - Creates Alert instances

## Test Examples

### Model Tests
```python
@pytest.mark.django_db
class TestTeamModel:
    def test_team_creation(self):
        team = TeamFactory(name="Test Team")
        assert team.name == "Test Team"
        assert team.is_active is False
```

### Service Tests
```python
@pytest.mark.django_db
class TestSlotScheduler:
    def test_slot_scheduler_initialization(self, scheduler):
        assert scheduler.logger is not None
```

### API View Tests
```python
@pytest.mark.django_db
class TestTeamViews:
    def test_list_teams_authenticated_admin(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/managers/teams-list/')
        assert response.status_code == 200
```

## Important Notes

1. **Database Access**: All tests that interact with the database must use the `@pytest.mark.django_db` decorator.

2. **Test Isolation**: Each test runs in isolation with a clean database state.

3. **Factory Usage**: Use factory classes instead of directly creating model instances for consistent test data.

4. **Time Zones**: When working with datetime fields, ensure you use timezone-aware datetimes.

## Dependencies

The testing setup requires these packages (already in requirements):
- `pytest==7.4.0`
- `pytest-django==4.5.2`
- `pytest-sugar==0.9.7`
- `factory-boy==3.2.1`

## Running Tests in CI/CD

For automated testing, you can run:

```bash
# Run all tests with coverage reporting
docker-compose -f local.yml exec django python -m pytest --cov=hirethon_template/managers hirethon_template/managers/tests/

# Run tests and generate coverage report
docker-compose -f local.yml exec django python -m pytest --cov=hirethon_template/managers --cov-report=html hirethon_template/managers/tests/
```
