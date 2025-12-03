from typing import List
from bot.database.db import db
from bot.database.models import Event


class EventService:
    """
    Business logic layer for event operations.
    Provides high-level functions for event management.
    """

    @staticmethod
    async def create_event(
            title: str,
            date: str,
            time: str,
            location: str,
            description: str,
            created_by: int
    ) -> Event:
        """
        Create a new event with validation.
        Returns the created event with ID.
        """
        event = Event(
            title=title,
            date=date,
            time=time,
            location=location,
            description=description,
            created_by=created_by
        )

        event_id = await db.add_event(event)
        event.id = event_id
        return event

    @staticmethod
    async def get_upcoming_events(days: int = 7) -> List[Event]:
        """
        Get events happening in the next N days.
        Default is 7 days (one week).
        """
        if days == 0:
            return await db.get_events_today()
        elif days == 7:
            return await db.get_events_week()
        else:
            return await db.get_all_events()

    @staticmethod
    async def search_events_by_keyword(keyword: str) -> List[Event]:
        """
        Search events by keyword in title or description.
        (Future enhancement - not yet implemented in DB layer)
        """
        all_events = await db.get_all_events()
        keyword_lower = keyword.lower()

        matching_events = [
            event for event in all_events
            if keyword_lower in event.title.lower() or
               keyword_lower in event.description.lower()
        ]

        return matching_events

    @staticmethod
    async def format_events_list(events: List[Event], include_description: bool = False) -> str:
        """
        Format a list of events into a readable message.
        """
        if not events:
            return "No events found."

        result = ""
        for event in events:
            result += f"📅 **{event.title}**\n"
            result += f"   📆 {event.date} at {event.time}\n"
            result += f"   📍 {event.location}\n"

            if include_description and event.description:
                result += f"   📝 {event.description}\n"

            result += "\n"

        return result


# Global service instance
event_service = EventService()