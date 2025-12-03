from datetime import datetime
from typing import Optional


class Event:
    """
    Event data model representing a university event.
    """

    def __init__(
            self,
            id: Optional[int] = None,
            title: str = "",
            date: str = "",
            time: str = "",
            location: str = "",
            description: str = "",
            created_by: int = 0,
            created_at: Optional[datetime] = None,
            updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.title = title
        self.date = date
        self.time = time
        self.location = location
        self.description = description
        self.created_by = created_by
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def to_dict(self) -> dict:
        """Convert event to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "date": self.date,
            "time": self.time,
            "location": self.location,
            "description": self.description,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def format_message(self) -> str:
        """Format event as a readable message"""
        msg = f"📅 **{self.title}**\n\n"
        msg += f"📆 Date: {self.date}\n"
        msg += f"🕐 Time: {self.time}\n"
        msg += f"📍 Location: {self.location}\n"
        if self.description:
            msg += f"\n📝 Description:\n{self.description}"
        return msg