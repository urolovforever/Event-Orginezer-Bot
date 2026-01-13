"""Comprehensive tests for the database module."""
import pytest
from datetime import datetime, timedelta
import pytz


# Configure pytest-asyncio
pytestmark = pytest.mark.asyncio


class TestDatabaseInitialization:
    """Tests for database initialization."""

    async def test_init_db_creates_tables(self, database):
        """Test that init_db creates all required tables."""
        import aiosqlite

        async with aiosqlite.connect(database.db_path) as db:
            # Check users table exists
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
            ) as cursor:
                result = await cursor.fetchone()
                assert result is not None, "users table should exist"

            # Check events table exists
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='events'"
            ) as cursor:
                result = await cursor.fetchone()
                assert result is not None, "events table should exist"

            # Check reminders table exists
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='reminders'"
            ) as cursor:
                result = await cursor.fetchone()
                assert result is not None, "reminders table should exist"

            # Check departments table exists
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='departments'"
            ) as cursor:
                result = await cursor.fetchone()
                assert result is not None, "departments table should exist"

    async def test_init_db_creates_default_departments(self, database, mock_config):
        """Test that init_db populates default departments."""
        departments = await database.get_all_departments()
        assert len(departments) == len(mock_config.DEPARTMENTS)
        for dept in mock_config.DEPARTMENTS:
            assert dept in departments

    async def test_init_db_idempotent(self, database):
        """Test that calling init_db multiple times doesn't duplicate data."""
        initial_count = len(await database.get_all_departments())

        # Call init_db again
        await database.init_db()

        # Should have same number of departments
        final_count = len(await database.get_all_departments())
        assert initial_count == final_count


class TestTimezoneConversion:
    """Tests for UTC to local timezone conversion."""

    async def test_convert_utc_to_local_valid(self, database):
        """Test conversion of valid UTC timestamp."""
        # UTC time 12:00 should be 17:00 in Tashkent (UTC+5)
        utc_timestamp = "2024-06-15 12:00:00"
        result = database._convert_utc_to_local(utc_timestamp)

        # Parse result to verify
        local_dt = datetime.strptime(result, '%Y-%m-%d %H:%M:%S')
        assert local_dt.hour == 17  # UTC+5

    async def test_convert_utc_to_local_midnight(self, database):
        """Test conversion at midnight UTC."""
        utc_timestamp = "2024-06-15 00:00:00"
        result = database._convert_utc_to_local(utc_timestamp)

        local_dt = datetime.strptime(result, '%Y-%m-%d %H:%M:%S')
        assert local_dt.hour == 5  # Midnight UTC = 5 AM in Tashkent

    async def test_convert_utc_to_local_date_change(self, database):
        """Test conversion that crosses date boundary."""
        # 20:00 UTC = 01:00 next day in Tashkent
        utc_timestamp = "2024-06-15 20:00:00"
        result = database._convert_utc_to_local(utc_timestamp)

        local_dt = datetime.strptime(result, '%Y-%m-%d %H:%M:%S')
        assert local_dt.day == 16  # Should be next day
        assert local_dt.hour == 1

    async def test_convert_utc_to_local_invalid_format(self, database):
        """Test conversion with invalid format returns original."""
        invalid_timestamp = "not-a-timestamp"
        result = database._convert_utc_to_local(invalid_timestamp)
        assert result == invalid_timestamp

    async def test_convert_utc_to_local_empty_string(self, database):
        """Test conversion with empty string."""
        result = database._convert_utc_to_local("")
        assert result == ""


class TestUserOperations:
    """Tests for user CRUD operations."""

    async def test_add_user_success(self, database, sample_user_data):
        """Test adding a new user successfully."""
        result = await database.add_user(**sample_user_data)
        assert result is True

    async def test_add_user_duplicate_fails(self, database, sample_user_data):
        """Test adding a duplicate user fails."""
        await database.add_user(**sample_user_data)
        # Try to add same user again
        result = await database.add_user(**sample_user_data)
        assert result is False

    async def test_add_user_admin_status_assigned(self, database, mock_config):
        """Test that admin status is correctly assigned."""
        admin_id = mock_config.ADMIN_USER_IDS[0]
        await database.add_user(
            telegram_id=admin_id,
            full_name="Admin User",
            department="IT Department",
            phone="+998900000000"
        )

        user = await database.get_user(admin_id)
        assert user['is_admin'] == 1

    async def test_add_user_non_admin_status(self, database, mock_config):
        """Test that non-admin users get is_admin=0."""
        non_admin_id = 99999  # Not in ADMIN_USER_IDS
        await database.add_user(
            telegram_id=non_admin_id,
            full_name="Regular User",
            department="IT Department",
            phone="+998900000001"
        )

        user = await database.get_user(non_admin_id)
        assert user['is_admin'] == 0

    async def test_get_user_existing(self, database_with_user):
        """Test getting an existing user."""
        user = await database_with_user.get_user(11111)
        assert user is not None
        assert user['full_name'] == "Test User"
        assert user['department'] == "IT Department"
        assert user['phone'] == "+998901234567"

    async def test_get_user_non_existing(self, database):
        """Test getting a non-existing user returns None."""
        user = await database.get_user(99999)
        assert user is None

    async def test_is_user_registered_true(self, database_with_user):
        """Test is_user_registered returns True for existing user."""
        result = await database_with_user.is_user_registered(11111)
        assert result is True

    async def test_is_user_registered_false(self, database):
        """Test is_user_registered returns False for non-existing user."""
        result = await database.is_user_registered(99999)
        assert result is False

    async def test_is_admin_true(self, database_with_admin):
        """Test is_admin returns True for admin user."""
        result = await database_with_admin.is_admin(12345)
        assert result is True

    async def test_is_admin_false_regular_user(self, database_with_user):
        """Test is_admin returns False for regular user."""
        result = await database_with_user.is_admin(11111)
        assert result is False

    async def test_is_admin_false_non_existing(self, database):
        """Test is_admin returns falsy for non-existing user.

        Note: The function returns None (falsy) rather than False for
        non-existing users due to Python short-circuit evaluation.
        """
        result = await database.is_admin(99999)
        assert not result  # Returns None, which is falsy


class TestEventOperations:
    """Tests for event CRUD operations."""

    async def test_add_event_success(self, database_with_user, sample_event_data):
        """Test adding a new event successfully."""
        event_id = await database_with_user.add_event(**sample_event_data)
        assert event_id is not None
        assert event_id > 0

    async def test_add_event_returns_unique_ids(self, database_with_user, sample_event_data):
        """Test that each event gets a unique ID."""
        event_id_1 = await database_with_user.add_event(**sample_event_data)

        sample_event_data['title'] = "Different Event"
        event_id_2 = await database_with_user.add_event(**sample_event_data)

        assert event_id_1 != event_id_2

    async def test_add_event_with_empty_comment(self, database_with_user):
        """Test adding event with empty comment."""
        event_id = await database_with_user.add_event(
            title="No Comment Event",
            date="20.06.2026",
            time="10:00",
            place="Room A",
            comment="",
            created_by_user_id=11111
        )
        assert event_id is not None

        event = await database_with_user.get_event(event_id)
        assert event['comment'] == ""

    async def test_add_event_with_none_comment(self, database_with_user):
        """Test adding event with None comment."""
        event_id = await database_with_user.add_event(
            title="None Comment Event",
            date="20.06.2026",
            time="10:00",
            place="Room A",
            comment=None,
            created_by_user_id=11111
        )
        assert event_id is not None

    async def test_get_event_existing(self, database_with_events):
        """Test getting an existing event."""
        event = await database_with_events.get_event(1)
        assert event is not None
        assert event['title'] == "Future Conference"
        assert event['creator_name'] == "Test User"

    async def test_get_event_includes_creator_info(self, database_with_events):
        """Test that get_event includes creator information."""
        event = await database_with_events.get_event(1)
        assert 'creator_name' in event
        assert 'creator_department' in event
        assert 'creator_phone' in event

    async def test_get_event_non_existing(self, database_with_user):
        """Test getting a non-existing event returns None."""
        event = await database_with_user.get_event(99999)
        assert event is None

    async def test_get_upcoming_events(self, database_with_events):
        """Test getting upcoming events."""
        events = await database_with_events.get_upcoming_events()
        assert len(events) >= 2

    async def test_get_upcoming_events_with_limit(self, database_with_events):
        """Test getting upcoming events with limit."""
        events = await database_with_events.get_upcoming_events(limit=1)
        assert len(events) == 1

    async def test_get_upcoming_events_excludes_cancelled(self, database_with_events):
        """Test that cancelled events are excluded from upcoming."""
        # Cancel an event
        await database_with_events.cancel_event(1)

        events = await database_with_events.get_upcoming_events()
        event_ids = [e['id'] for e in events]
        assert 1 not in event_ids

    async def test_get_events_by_date(self, database_with_events):
        """Test getting events by specific date."""
        events = await database_with_events.get_events_by_date("25.12.2026")
        assert len(events) == 1
        assert events[0]['title'] == "Future Conference"

    async def test_get_events_by_date_no_results(self, database_with_events):
        """Test getting events for date with no events."""
        events = await database_with_events.get_events_by_date("01.01.2020")
        assert len(events) == 0

    async def test_get_events_by_date_excludes_cancelled(self, database_with_events):
        """Test that cancelled events are excluded by date query."""
        await database_with_events.cancel_event(1)

        events = await database_with_events.get_events_by_date("25.12.2026")
        assert len(events) == 0


class TestEventsByUser:
    """Tests for get_events_by_user with upcoming_only filter."""

    async def test_get_events_by_user_all(self, database_with_events):
        """Test getting all events by user."""
        events = await database_with_events.get_events_by_user(11111, upcoming_only=False)
        assert len(events) >= 2

    async def test_get_events_by_user_upcoming_only(self, database_with_events):
        """Test getting only upcoming events by user."""
        events = await database_with_events.get_events_by_user(11111, upcoming_only=True)
        # All events in fixture are in 2026, so they should be upcoming
        assert len(events) >= 2

    async def test_get_events_by_user_no_events(self, database_with_events):
        """Test user with no events."""
        # Add another user
        await database_with_events.add_user(
            telegram_id=44444,
            full_name="Empty User",
            department="HR Department",
            phone="+998901112233"
        )

        events = await database_with_events.get_events_by_user(44444, upcoming_only=False)
        assert len(events) == 0

    async def test_get_events_by_user_excludes_cancelled(self, database_with_events):
        """Test that cancelled events are excluded."""
        initial_events = await database_with_events.get_events_by_user(11111, upcoming_only=False)
        initial_count = len(initial_events)

        await database_with_events.cancel_event(1)

        events = await database_with_events.get_events_by_user(11111, upcoming_only=False)
        assert len(events) == initial_count - 1


class TestEventsByDateRange:
    """Tests for get_events_by_date_range."""

    async def test_get_events_by_date_range_inclusive(self, database_with_events):
        """Test date range includes boundary dates."""
        events = await database_with_events.get_events_by_date_range(
            start_date="20.12.2026",
            end_date="25.12.2026"
        )
        assert len(events) == 2  # Both events should be included

    async def test_get_events_by_date_range_start_boundary(self, database_with_events):
        """Test start date boundary is inclusive."""
        events = await database_with_events.get_events_by_date_range(
            start_date="20.12.2026",
            end_date="20.12.2026"
        )
        assert len(events) == 1
        assert events[0]['date'] == "20.12.2026"

    async def test_get_events_by_date_range_end_boundary(self, database_with_events):
        """Test end date boundary is inclusive."""
        events = await database_with_events.get_events_by_date_range(
            start_date="25.12.2026",
            end_date="25.12.2026"
        )
        assert len(events) == 1
        assert events[0]['date'] == "25.12.2026"

    async def test_get_events_by_date_range_no_results(self, database_with_events):
        """Test date range with no events."""
        events = await database_with_events.get_events_by_date_range(
            start_date="01.01.2020",
            end_date="31.12.2020"
        )
        assert len(events) == 0

    async def test_get_events_by_date_range_invalid_format(self, database_with_events):
        """Test with invalid date format returns empty list."""
        events = await database_with_events.get_events_by_date_range(
            start_date="invalid",
            end_date="also-invalid"
        )
        assert len(events) == 0

    async def test_get_events_by_date_range_excludes_cancelled(self, database_with_events):
        """Test that cancelled events are excluded from range."""
        await database_with_events.cancel_event(1)

        events = await database_with_events.get_events_by_date_range(
            start_date="20.12.2026",
            end_date="31.12.2026"
        )
        event_ids = [e['id'] for e in events]
        assert 1 not in event_ids


class TestUpdateEvent:
    """Tests for update_event."""

    async def test_update_event_title(self, database_with_events):
        """Test updating event title."""
        result = await database_with_events.update_event(1, title="Updated Title")
        assert result is True

        event = await database_with_events.get_event(1)
        assert event['title'] == "Updated Title"

    async def test_update_event_multiple_fields(self, database_with_events):
        """Test updating multiple event fields."""
        result = await database_with_events.update_event(
            1,
            title="New Title",
            date="30.12.2026",
            time="16:00",
            place="New Place"
        )
        assert result is True

        event = await database_with_events.get_event(1)
        assert event['title'] == "New Title"
        assert event['date'] == "30.12.2026"
        assert event['time'] == "16:00"
        assert event['place'] == "New Place"

    async def test_update_event_comment(self, database_with_events):
        """Test updating event comment."""
        result = await database_with_events.update_event(1, comment="New comment")
        assert result is True

        event = await database_with_events.get_event(1)
        assert event['comment'] == "New comment"

    async def test_update_event_no_fields(self, database_with_events):
        """Test updating with no valid fields returns False."""
        result = await database_with_events.update_event(1)
        assert result is False

    async def test_update_event_invalid_field_ignored(self, database_with_events):
        """Test that invalid fields are ignored."""
        original_event = await database_with_events.get_event(1)

        result = await database_with_events.update_event(
            1,
            invalid_field="should be ignored",
            title="Valid Update"
        )
        assert result is True

        event = await database_with_events.get_event(1)
        assert event['title'] == "Valid Update"

    async def test_update_event_clears_reminders(self, database_with_events):
        """Test that updating event clears old reminders."""
        # Add a reminder first
        await database_with_events.add_reminder(1, "24h")

        # Verify reminder exists
        assert await database_with_events.is_reminder_sent(1, "24h") is True

        # Update the event
        await database_with_events.update_event(1, time="18:00")

        # Reminder should be cleared
        assert await database_with_events.is_reminder_sent(1, "24h") is False


class TestCancelAndDeleteEvent:
    """Tests for cancel_event and delete_event."""

    async def test_cancel_event_success(self, database_with_events):
        """Test cancelling an event."""
        result = await database_with_events.cancel_event(1)
        assert result is True

        # Event should still exist but be cancelled
        event = await database_with_events.get_event(1)
        assert event['is_cancelled'] == 1

    async def test_cancel_event_excludes_from_queries(self, database_with_events):
        """Test that cancelled events are excluded from queries."""
        await database_with_events.cancel_event(1)

        # Should not appear in upcoming events
        events = await database_with_events.get_upcoming_events()
        event_ids = [e['id'] for e in events]
        assert 1 not in event_ids

    async def test_delete_event_success(self, database_with_events):
        """Test permanently deleting an event."""
        result = await database_with_events.delete_event(1)
        assert result is True

        # Event should be gone
        event = await database_with_events.get_event(1)
        assert event is None

    async def test_delete_event_non_existing(self, database_with_events):
        """Test deleting non-existing event."""
        result = await database_with_events.delete_event(99999)
        # SQLite DELETE doesn't fail for non-existing rows
        assert result is True


class TestReminderOperations:
    """Tests for reminder tracking operations."""

    async def test_add_reminder_success(self, database_with_events):
        """Test adding a reminder record."""
        result = await database_with_events.add_reminder(1, "24h")
        assert result is True

    async def test_add_multiple_reminder_types(self, database_with_events):
        """Test adding different reminder types for same event."""
        await database_with_events.add_reminder(1, "24h")
        await database_with_events.add_reminder(1, "3h")
        await database_with_events.add_reminder(1, "1h")

        assert await database_with_events.is_reminder_sent(1, "24h") is True
        assert await database_with_events.is_reminder_sent(1, "3h") is True
        assert await database_with_events.is_reminder_sent(1, "1h") is True

    async def test_is_reminder_sent_true(self, database_with_events):
        """Test is_reminder_sent returns True when sent."""
        await database_with_events.add_reminder(1, "24h")
        result = await database_with_events.is_reminder_sent(1, "24h")
        assert result is True

    async def test_is_reminder_sent_false(self, database_with_events):
        """Test is_reminder_sent returns False when not sent."""
        result = await database_with_events.is_reminder_sent(1, "24h")
        assert result is False

    async def test_is_reminder_sent_different_type(self, database_with_events):
        """Test that different reminder types are tracked separately."""
        await database_with_events.add_reminder(1, "24h")

        assert await database_with_events.is_reminder_sent(1, "24h") is True
        assert await database_with_events.is_reminder_sent(1, "3h") is False

    async def test_is_reminder_sent_different_event(self, database_with_events):
        """Test that reminders are tracked per event."""
        await database_with_events.add_reminder(1, "24h")

        assert await database_with_events.is_reminder_sent(1, "24h") is True
        assert await database_with_events.is_reminder_sent(2, "24h") is False


class TestStatistics:
    """Tests for statistics operations."""

    async def test_get_event_count_by_department(self, database_with_events):
        """Test getting event count grouped by department."""
        stats = await database_with_events.get_event_count_by_department()
        assert len(stats) > 0

        # Find IT Department
        it_stats = next((s for s in stats if s['department'] == "IT Department"), None)
        assert it_stats is not None
        assert it_stats['event_count'] >= 2

    async def test_get_event_count_by_department_excludes_cancelled(self, database_with_events):
        """Test that cancelled events don't count in stats."""
        initial_stats = await database_with_events.get_event_count_by_department()
        initial_count = next(
            (s['event_count'] for s in initial_stats if s['department'] == "IT Department"),
            0
        )

        await database_with_events.cancel_event(1)

        stats = await database_with_events.get_event_count_by_department()
        new_count = next(
            (s['event_count'] for s in stats if s['department'] == "IT Department"),
            0
        )

        assert new_count == initial_count - 1

    async def test_get_total_events_count(self, database_with_events):
        """Test getting total events count."""
        count = await database_with_events.get_total_events_count()
        assert count >= 2

    async def test_get_total_events_count_excludes_cancelled(self, database_with_events):
        """Test that cancelled events don't count in total."""
        initial_count = await database_with_events.get_total_events_count()

        await database_with_events.cancel_event(1)

        new_count = await database_with_events.get_total_events_count()
        assert new_count == initial_count - 1

    async def test_get_total_events_count_empty_db(self, database):
        """Test total count on empty database."""
        count = await database.get_total_events_count()
        assert count == 0


class TestDepartmentOperations:
    """Tests for department management operations."""

    async def test_get_all_departments_active_only(self, database):
        """Test getting only active departments."""
        departments = await database.get_all_departments(active_only=True)
        assert len(departments) > 0

    async def test_get_all_departments_include_inactive(self, database):
        """Test getting all departments including inactive."""
        # Deactivate one department
        await database.delete_department("IT Department")

        active_depts = await database.get_all_departments(active_only=True)
        all_depts = await database.get_all_departments(active_only=False)

        assert len(all_depts) > len(active_depts)

    async def test_get_all_departments_sorted(self, database):
        """Test that departments are sorted alphabetically."""
        departments = await database.get_all_departments()
        sorted_depts = sorted(departments)
        assert departments == sorted_depts

    async def test_add_department_success(self, database):
        """Test adding a new department."""
        result = await database.add_department("New Department")
        assert result is True

        departments = await database.get_all_departments()
        assert "New Department" in departments

    async def test_add_department_duplicate_fails(self, database):
        """Test adding duplicate department fails."""
        await database.add_department("Unique Department")
        result = await database.add_department("Unique Department")
        assert result is False

    async def test_delete_department_soft_delete(self, database):
        """Test that delete is a soft delete."""
        await database.add_department("To Delete")
        result = await database.delete_department("To Delete")
        assert result is True

        # Should not appear in active departments
        active_depts = await database.get_all_departments(active_only=True)
        assert "To Delete" not in active_depts

        # Should still appear in all departments
        all_depts = await database.get_all_departments(active_only=False)
        assert "To Delete" in all_depts

    async def test_delete_department_non_existing(self, database):
        """Test deleting non-existing department."""
        result = await database.delete_department("Non Existing Department")
        # SQLite UPDATE doesn't fail for non-matching rows
        assert result is True


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    async def test_unicode_in_user_name(self, database):
        """Test unicode characters in user name."""
        result = await database.add_user(
            telegram_id=55555,
            full_name="Ўзбек Фойдаланувчи",  # Uzbek Cyrillic
            department="IT Department",
            phone="+998901234567"
        )
        assert result is True

        user = await database.get_user(55555)
        assert user['full_name'] == "Ўзбек Фойдаланувчи"

    async def test_unicode_in_event_title(self, database_with_user):
        """Test unicode characters in event title."""
        event_id = await database_with_user.add_event(
            title="Конференция 2026",  # Russian
            date="15.06.2026",
            time="10:00",
            place="Зал А",
            comment="Тест",
            created_by_user_id=11111
        )
        assert event_id is not None

        event = await database_with_user.get_event(event_id)
        assert event['title'] == "Конференция 2026"

    async def test_special_characters_in_comment(self, database_with_user):
        """Test special characters in comment."""
        event_id = await database_with_user.add_event(
            title="Test Event",
            date="15.06.2026",
            time="10:00",
            place="Room A",
            comment="Special chars: <>&\"'@#$%^*()[]{}|\\",
            created_by_user_id=11111
        )
        assert event_id is not None

        event = await database_with_user.get_event(event_id)
        assert "<>" in event['comment']

    async def test_very_long_title(self, database_with_user):
        """Test handling of very long titles."""
        long_title = "A" * 1000
        event_id = await database_with_user.add_event(
            title=long_title,
            date="15.06.2026",
            time="10:00",
            place="Room A",
            comment="Test",
            created_by_user_id=11111
        )
        assert event_id is not None

        event = await database_with_user.get_event(event_id)
        assert len(event['title']) == 1000

    async def test_time_edge_midnight(self, database_with_user):
        """Test event at midnight."""
        event_id = await database_with_user.add_event(
            title="Midnight Event",
            date="15.06.2026",
            time="00:00",
            place="Room A",
            comment="Test",
            created_by_user_id=11111
        )
        assert event_id is not None

        event = await database_with_user.get_event(event_id)
        assert event['time'] == "00:00"

    async def test_time_edge_end_of_day(self, database_with_user):
        """Test event at 23:59."""
        event_id = await database_with_user.add_event(
            title="Late Night Event",
            date="15.06.2026",
            time="23:59",
            place="Room A",
            comment="Test",
            created_by_user_id=11111
        )
        assert event_id is not None

        event = await database_with_user.get_event(event_id)
        assert event['time'] == "23:59"

    async def test_leap_year_date(self, database_with_user):
        """Test event on leap year date."""
        event_id = await database_with_user.add_event(
            title="Leap Year Event",
            date="29.02.2028",  # 2028 is a leap year
            time="10:00",
            place="Room A",
            comment="Test",
            created_by_user_id=11111
        )
        assert event_id is not None

        event = await database_with_user.get_event(event_id)
        assert event['date'] == "29.02.2028"

    async def test_year_end_date_range(self, database_with_user):
        """Test date range spanning year boundary."""
        # Add event at end of year
        await database_with_user.add_event(
            title="Year End Event",
            date="31.12.2026",
            time="23:00",
            place="Room A",
            comment="Test",
            created_by_user_id=11111
        )

        # Add event at start of next year
        await database_with_user.add_event(
            title="New Year Event",
            date="01.01.2027",
            time="10:00",
            place="Room A",
            comment="Test",
            created_by_user_id=11111
        )

        events = await database_with_user.get_events_by_date_range(
            start_date="31.12.2026",
            end_date="01.01.2027"
        )
        assert len(events) == 2

    async def test_large_telegram_id(self, database):
        """Test handling of large Telegram IDs."""
        large_id = 8423839879  # Real example from config
        result = await database.add_user(
            telegram_id=large_id,
            full_name="Large ID User",
            department="IT Department",
            phone="+998901234567"
        )
        assert result is True

        user = await database.get_user(large_id)
        assert user['telegram_id'] == large_id

    async def test_negative_telegram_id_handling(self, database):
        """Test handling of negative IDs (group chats have negative IDs)."""
        # Note: User IDs shouldn't be negative, but we test robustness
        negative_id = -123456
        result = await database.add_user(
            telegram_id=negative_id,
            full_name="Negative ID User",
            department="IT Department",
            phone="+998901234567"
        )
        assert result is True

        user = await database.get_user(negative_id)
        assert user['telegram_id'] == negative_id


class TestConcurrentOperations:
    """Tests for concurrent database operations."""

    async def test_multiple_events_same_datetime(self, database_with_user):
        """Test creating multiple events at the same date/time."""
        event1_id = await database_with_user.add_event(
            title="Event 1",
            date="15.06.2026",
            time="10:00",
            place="Room A",
            comment="First",
            created_by_user_id=11111
        )

        event2_id = await database_with_user.add_event(
            title="Event 2",
            date="15.06.2026",
            time="10:00",
            place="Room B",
            comment="Second",
            created_by_user_id=11111
        )

        assert event1_id != event2_id
        assert event1_id is not None
        assert event2_id is not None

        # Both should appear in date query
        events = await database_with_user.get_events_by_date("15.06.2026")
        assert len(events) == 2

    async def test_reminder_for_multiple_events(self, database_with_events):
        """Test reminders are tracked separately per event."""
        await database_with_events.add_reminder(1, "24h")
        await database_with_events.add_reminder(2, "24h")

        assert await database_with_events.is_reminder_sent(1, "24h") is True
        assert await database_with_events.is_reminder_sent(2, "24h") is True

        # Different type for event 1 should be False
        assert await database_with_events.is_reminder_sent(1, "3h") is False
