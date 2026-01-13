"""Pytest configuration and fixtures for Event Organizer Bot tests."""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from datetime import datetime
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def mock_config():
    """Mock config module to avoid requiring environment variables."""
    mock_cfg = MagicMock()
    mock_cfg.DATABASE_PATH = ":memory:"
    mock_cfg.TIMEZONE = "Asia/Tashkent"
    mock_cfg.ADMIN_USER_IDS = [12345, 67890]
    mock_cfg.ALLOWED_USER_IDS = [12345, 67890, 11111, 22222]
    mock_cfg.DEPARTMENTS = [
        "IT Department",
        "HR Department",
        "Finance Department"
    ]
    mock_cfg.REMINDER_HOURS = [24, 3, 1, 0.5, 0.1667]

    with patch.dict(sys.modules, {'config': mock_cfg}):
        yield mock_cfg


@pytest.fixture
def temp_db_path():
    """Create a temporary database file path."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
async def database(temp_db_path, mock_config):
    """Create a test database instance with initialized tables."""
    # Import after mocking config
    from database import Database

    db = Database(db_path=temp_db_path)
    await db.init_db()
    yield db


@pytest.fixture
async def database_with_user(database, mock_config):
    """Database with a pre-created test user."""
    await database.add_user(
        telegram_id=11111,
        full_name="Test User",
        department="IT Department",
        phone="+998901234567"
    )
    yield database


@pytest.fixture
async def database_with_admin(database, mock_config):
    """Database with a pre-created admin user."""
    await database.add_user(
        telegram_id=12345,  # This is in ADMIN_USER_IDS
        full_name="Admin User",
        department="IT Department",
        phone="+998909999999"
    )
    yield database


@pytest.fixture
async def database_with_events(database_with_user, mock_config):
    """Database with pre-created test events."""
    # Future event
    await database_with_user.add_event(
        title="Future Conference",
        date="25.12.2026",
        time="14:00",
        place="Main Hall",
        comment="Annual conference",
        created_by_user_id=11111
    )

    # Another future event
    await database_with_user.add_event(
        title="Team Meeting",
        date="20.12.2026",
        time="10:00",
        place="Meeting Room A",
        comment="Weekly sync",
        created_by_user_id=11111
    )

    yield database_with_user


@pytest.fixture
def sample_event_data():
    """Sample event data for testing."""
    return {
        "title": "Test Event",
        "date": "15.06.2026",
        "time": "15:30",
        "place": "Conference Room B",
        "comment": "Test comment",
        "created_by_user_id": 11111
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "telegram_id": 33333,
        "full_name": "Sample User",
        "department": "HR Department",
        "phone": "+998901112233"
    }
