import aiosqlite
from datetime import datetime, timedelta
from typing import List, Optional
from bot.config import Config
from bot.database.models import Event


class Database:
    """
    Database handler for event storage and retrieval.
    Uses SQLite with async support.
    """

    def __init__(self, db_path: str = Config.DATABASE_PATH):
        self.db_path = db_path

    async def init_db(self):
        """
        Initialize database and create tables if they don't exist.
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    location TEXT NOT NULL,
                    description TEXT,
                    created_by INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Create index for faster date queries
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_date 
                ON events(date)
            """)

            await db.commit()

    async def add_event(self, event: Event) -> int:
        """
        Add a new event to the database.
        Returns the ID of the created event.
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO events 
                (title, date, time, location, description, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.title,
                event.date,
                event.time,
                event.location,
                event.description,
                event.created_by,
                event.created_at.isoformat(),
                event.updated_at.isoformat()
            ))
            await db.commit()
            return cursor.lastrowid

    async def get_event(self, event_id: int) -> Optional[Event]:
        """Get a single event by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM events WHERE id = ?",
                (event_id,)
            )
            row = await cursor.fetchone()
            if row:
                return self._row_to_event(row)
            return None

    async def get_events_today(self) -> List[Event]:
        """Get all events happening today"""
        today = datetime.now().strftime("%Y-%m-%d")
        return await self.get_events_by_date(today)

    async def get_events_week(self) -> List[Event]:
        """Get all events happening in the next 7 days"""
        today = datetime.now()
        week_later = today + timedelta(days=7)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM events 
                WHERE date >= ? AND date <= ?
                ORDER BY date, time
            """, (
                today.strftime("%Y-%m-%d"),
                week_later.strftime("%Y-%m-%d")
            ))
            rows = await cursor.fetchall()
            return [self._row_to_event(row) for row in rows]

    async def get_all_events(self) -> List[Event]:
        """Get all upcoming events"""
        today = datetime.now().strftime("%Y-%m-%d")

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM events 
                WHERE date >= ?
                ORDER BY date, time
            """, (today,))
            rows = await cursor.fetchall()
            return [self._row_to_event(row) for row in rows]

    async def get_events_by_date(self, date: str) -> List[Event]:
        """Get all events on a specific date"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM events 
                WHERE date = ?
                ORDER BY time
            """, (date,))
            rows = await cursor.fetchall()
            return [self._row_to_event(row) for row in rows]

    async def update_event(self, event_id: int, field: str, value: str) -> bool:
        """
        Update a specific field of an event.
        Returns True if successful, False otherwise.
        """
        allowed_fields = ["title", "date", "time", "location", "description"]
        if field not in allowed_fields:
            return False

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"""
                UPDATE events 
                SET {field} = ?, updated_at = ?
                WHERE id = ?
            """, (value, datetime.now().isoformat(), event_id))
            await db.commit()
            return True

    async def delete_event(self, event_id: int) -> bool:
        """Delete an event by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM events WHERE id = ?",
                (event_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def get_events_for_reminders(self, hours: int) -> List[Event]:
        """
        Get events that should trigger reminders.
        Returns events happening in exactly 'hours' hours from now.
        """
        target_time = datetime.now() + timedelta(hours=hours)
        target_date = target_time.strftime("%Y-%m-%d")

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM events 
                WHERE date = ?
                ORDER BY time
            """, (target_date,))
            rows = await cursor.fetchall()
            events = [self._row_to_event(row) for row in rows]

            # Filter to get events within the hour window
            filtered_events = []
            for event in events:
                event_datetime = datetime.strptime(
                    f"{event.date} {event.time}",
                    "%Y-%m-%d %H:%M"
                )
                time_diff = (event_datetime - datetime.now()).total_seconds() / 3600

                # Check if event is within 1 hour of target time
                if hours - 1 <= time_diff <= hours + 1:
                    filtered_events.append(event)

            return filtered_events

    @staticmethod
    def _row_to_event(row: aiosqlite.Row) -> Event:
        """Convert database row to Event object"""
        return Event(
            id=row["id"],
            title=row["title"],
            date=row["date"],
            time=row["time"],
            location=row["location"],
            description=row["description"] or "",
            created_by=row["created_by"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
        )


# Global database instance
db = Database()