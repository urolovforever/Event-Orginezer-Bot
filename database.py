"""Database module for the Event Organizer Bot."""
import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict, Any
import config
import pytz


class Database:
    """Database handler for SQLite operations."""

    def __init__(self, db_path: str = config.DATABASE_PATH):
        """Initialize database connection."""
        self.db_path = db_path

    def _convert_utc_to_local(self, utc_timestamp_str: str) -> str:
        """Convert UTC timestamp string to local timezone."""
        try:
            # Parse UTC timestamp
            utc_dt = datetime.strptime(utc_timestamp_str, '%Y-%m-%d %H:%M:%S')
            utc_dt = pytz.utc.localize(utc_dt)

            # Convert to local timezone
            local_tz = pytz.timezone(config.TIMEZONE)
            local_dt = utc_dt.astimezone(local_tz)

            # Return formatted string
            return local_dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"Error converting timestamp: {e}")
            return utc_timestamp_str

    async def init_db(self):
        """Initialize database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    department TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    is_admin INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Events table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    place TEXT NOT NULL,
                    comment TEXT,
                    created_by_user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_cancelled INTEGER DEFAULT 0,
                    FOREIGN KEY (created_by_user_id) REFERENCES users(telegram_id)
                )
            ''')

            # Reminders table (to track sent reminders)
            await db.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    reminder_type TEXT NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES events(id)
                )
            ''')

            # Departments table (for admin management)
            await db.execute('''
                CREATE TABLE IF NOT EXISTS departments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            await db.commit()

            # Insert default departments if table is empty
            async with db.execute('SELECT COUNT(*) FROM departments') as cursor:
                count = (await cursor.fetchone())[0]
                if count == 0:
                    for dept in config.DEPARTMENTS:
                        await db.execute(
                            'INSERT INTO departments (name) VALUES (?)',
                            (dept,)
                        )
                    await db.commit()

    # User CRUD operations
    async def add_user(self, telegram_id: int, full_name: str, department: str, phone: str) -> bool:
        """Add a new user to the database."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                is_admin = 1 if telegram_id in config.ADMIN_USER_IDS else 0
                await db.execute(
                    'INSERT INTO users (telegram_id, full_name, department, phone, is_admin) VALUES (?, ?, ?, ?, ?)',
                    (telegram_id, full_name, department, phone, is_admin)
                )
                await db.commit()
                return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False

    async def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get user by telegram_id."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                'SELECT * FROM users WHERE telegram_id = ?',
                (telegram_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def is_user_registered(self, telegram_id: int) -> bool:
        """Check if user is registered."""
        user = await self.get_user(telegram_id)
        return user is not None

    async def is_admin(self, telegram_id: int) -> bool:
        """Check if user is admin."""
        user = await self.get_user(telegram_id)
        return user and user['is_admin'] == 1

    # Event CRUD operations
    async def add_event(self, title: str, date: str, time: str, place: str,
                       comment: str, created_by_user_id: int) -> Optional[int]:
        """Add a new event to the database."""
        try:
            # Get current time in Tashkent timezone
            local_tz = pytz.timezone(config.TIMEZONE)
            local_now = datetime.now(local_tz).strftime('%Y-%m-%d %H:%M:%S')

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    '''INSERT INTO events (title, date, time, place, comment, created_by_user_id, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (title, date, time, place, comment, created_by_user_id, local_now)
                )
                await db.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Error adding event: {e}")
            return None

    async def get_event(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Get event by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                '''SELECT e.*, u.full_name as creator_name, u.department as creator_department, u.phone as creator_phone
                   FROM events e
                   JOIN users u ON e.created_by_user_id = u.telegram_id
                   WHERE e.id = ?''',
                (event_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    event = dict(row)
                    # Convert UTC timestamp to local timezone
                    if 'created_at' in event and event['created_at']:
                        event['created_at'] = self._convert_utc_to_local(event['created_at'])
                    return event
                return None

    async def get_upcoming_events(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all upcoming events (not cancelled, date >= today)."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            today = datetime.now().strftime('%d.%m.%Y')

            query = '''SELECT e.*, u.full_name as creator_name, u.department as creator_department, u.phone as creator_phone
                      FROM events e
                      JOIN users u ON e.created_by_user_id = u.telegram_id
                      WHERE e.is_cancelled = 0
                      ORDER BY e.date, e.time'''

            if limit:
                query += f' LIMIT {limit}'

            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                events = []
                for row in rows:
                    event = dict(row)
                    # Convert UTC timestamp to local timezone
                    if 'created_at' in event and event['created_at']:
                        event['created_at'] = self._convert_utc_to_local(event['created_at'])
                    events.append(event)
                return events

    async def get_events_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Get events by specific date."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                '''SELECT e.*, u.full_name as creator_name, u.department as creator_department, u.phone as creator_phone
                   FROM events e
                   JOIN users u ON e.created_by_user_id = u.telegram_id
                   WHERE e.date = ? AND e.is_cancelled = 0
                   ORDER BY e.time''',
                (date,)
            ) as cursor:
                rows = await cursor.fetchall()
                events = []
                for row in rows:
                    event = dict(row)
                    # Convert UTC timestamp to local timezone
                    if 'created_at' in event and event['created_at']:
                        event['created_at'] = self._convert_utc_to_local(event['created_at'])
                    events.append(event)
                return events

    async def get_events_by_user(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Get all events created by a specific user."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                '''SELECT e.*, u.full_name as creator_name, u.department as creator_department, u.phone as creator_phone
                   FROM events e
                   JOIN users u ON e.created_by_user_id = u.telegram_id
                   WHERE e.created_by_user_id = ? AND e.is_cancelled = 0
                   ORDER BY e.date, e.time''',
                (telegram_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                events = []
                for row in rows:
                    event = dict(row)
                    # Convert UTC timestamp to local timezone
                    if 'created_at' in event and event['created_at']:
                        event['created_at'] = self._convert_utc_to_local(event['created_at'])
                    events.append(event)
                return events

    async def update_event(self, event_id: int, **kwargs) -> bool:
        """Update event fields."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Build update query dynamically
                fields = []
                values = []
                for key, value in kwargs.items():
                    if key in ['title', 'date', 'time', 'place', 'comment']:
                        fields.append(f"{key} = ?")
                        values.append(value)

                if not fields:
                    return False

                values.append(event_id)
                query = f"UPDATE events SET {', '.join(fields)} WHERE id = ?"

                await db.execute(query, values)
                await db.commit()
                return True
        except Exception as e:
            print(f"Error updating event: {e}")
            return False

    async def cancel_event(self, event_id: int) -> bool:
        """Cancel an event (soft delete)."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    'UPDATE events SET is_cancelled = 1 WHERE id = ?',
                    (event_id,)
                )
                await db.commit()
                return True
        except Exception as e:
            print(f"Error cancelling event: {e}")
            return False

    async def delete_event(self, event_id: int) -> bool:
        """Permanently delete an event."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('DELETE FROM events WHERE id = ?', (event_id,))
                await db.commit()
                return True
        except Exception as e:
            print(f"Error deleting event: {e}")
            return False

    # Reminder operations
    async def add_reminder(self, event_id: int, reminder_type: str) -> bool:
        """Record that a reminder has been sent."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    'INSERT INTO reminders (event_id, reminder_type) VALUES (?, ?)',
                    (event_id, reminder_type)
                )
                await db.commit()
                return True
        except Exception as e:
            print(f"Error adding reminder: {e}")
            return False

    async def is_reminder_sent(self, event_id: int, reminder_type: str) -> bool:
        """Check if a reminder has been sent for an event."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT id FROM reminders WHERE event_id = ? AND reminder_type = ?',
                (event_id, reminder_type)
            ) as cursor:
                row = await cursor.fetchone()
                return row is not None

    # Statistics
    async def get_event_count_by_department(self) -> List[Dict[str, Any]]:
        """Get event count grouped by department."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                '''SELECT u.department, COUNT(e.id) as event_count
                   FROM events e
                   JOIN users u ON e.created_by_user_id = u.telegram_id
                   WHERE e.is_cancelled = 0
                   GROUP BY u.department
                   ORDER BY event_count DESC'''
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_total_events_count(self) -> int:
        """Get total number of events."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT COUNT(*) as count FROM events WHERE is_cancelled = 0'
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    # Department operations
    async def get_all_departments(self, active_only: bool = True) -> List[str]:
        """Get all departments."""
        async with aiosqlite.connect(self.db_path) as db:
            query = 'SELECT name FROM departments'
            if active_only:
                query += ' WHERE is_active = 1'
            query += ' ORDER BY name'

            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def add_department(self, name: str) -> bool:
        """Add a new department."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    'INSERT INTO departments (name) VALUES (?)',
                    (name,)
                )
                await db.commit()
                return True
        except Exception as e:
            print(f"Error adding department: {e}")
            return False

    async def delete_department(self, name: str) -> bool:
        """Soft delete a department."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    'UPDATE departments SET is_active = 0 WHERE name = ?',
                    (name,)
                )
                await db.commit()
                return True
        except Exception as e:
            print(f"Error deleting department: {e}")
            return False


# Global database instance
db = Database()
