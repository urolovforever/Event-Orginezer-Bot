"""Scheduler module for event reminders."""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import pytz
import config
from database import db
from google_sheets import sheets_manager


class ReminderScheduler:
    """Scheduler for sending event reminders."""

    def __init__(self, bot):
        """Initialize the scheduler."""
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone(config.TIMEZONE))
        self.running = False

    def start(self):
        """Start the scheduler with two jobs: check reminders and mark past events."""
        if not self.running:
            # Job 1: Check reminders every 1 minute
            self.scheduler.add_job(
                self.check_reminders,
                trigger=IntervalTrigger(minutes=1),
                id='check_reminders',
                replace_existing=True
            )

            # Job 2: Mark past events daily at 00:05 AM
            self.scheduler.add_job(
                self.mark_past_events_job,
                trigger=CronTrigger(minute=1),
                id='mark_past_events',
                replace_existing=True
            )

            self.scheduler.start()
            self.running = True

    def stop(self):
        """Stop the scheduler."""
        if self.running:
            self.scheduler.shutdown()
            self.running = False

    async def check_reminders(self):
        """Check upcoming events and send reminders if necessary."""
        try:
            tz = pytz.timezone(config.TIMEZONE)
            now = datetime.now(tz)
            events = await db.get_upcoming_events()

            for event in events:
                await self._check_event_reminders(event, now)

        except Exception as e:
            print(f"❌ Error checking reminders: {e}")

    async def _check_event_reminders(self, event: dict, now: datetime):
        """Check and send reminders for a specific event."""
        try:
            event_datetime = self._parse_event_datetime(event['date'], event['time'])
            if not event_datetime:
                return

            # Skip past events
            if now >= event_datetime:
                return

            for hours_before in config.REMINDER_HOURS:
                reminder_time = event_datetime - timedelta(hours=hours_before)

                # Create reminder_type identifier based on time unit
                # For hours >= 1: use hours, for minutes use 'min' suffix
                if hours_before >= 1:
                    reminder_type = f"{hours_before}h_before"
                else:
                    # Convert to minutes for sub-hour reminders
                    minutes = int(hours_before * 60)
                    reminder_type = f"{minutes}min_before"

                time_diff = (reminder_time - now).total_seconds()

                # Send reminder if within next 60 seconds or already passed but not sent
                if 0 <= time_diff < 60 or (-3600 < time_diff < 0):  # 1 hour catch-up window
                    already_sent = await db.is_reminder_sent(event['id'], reminder_type)
                    if not already_sent:
                        await self._send_reminder(event, hours_before)
                        await db.add_reminder(event['id'], reminder_type)

        except Exception as e:
            print(f"❌ Error in _check_event_reminders: {e}")

    def _parse_event_datetime(self, date_str: str, time_str: str) -> Optional[datetime]:
        """Parse event date and time into a timezone-aware datetime object."""
        try:
            day, month, year = map(int, date_str.split('.'))
            hour, minute = map(int, time_str.split(':'))

            tz = pytz.timezone(config.TIMEZONE)
            dt = datetime(year, month, day, hour, minute)
            return tz.localize(dt)

        except Exception:
            return None

    async def _send_reminder(self, event: dict, hours_before: float):
        """Send reminder message to media group chat."""
        try:
            if not config.MEDIA_GROUP_CHAT_ID:
                return

            # Format time description in Uzbek based on the time unit
            if hours_before >= 24:
                # Display in days
                days = int(hours_before // 24)
                time_desc = f"{days} kun"
            elif hours_before >= 1:
                # Display in hours
                hours = int(hours_before)
                time_desc = f"{hours} soat"
            else:
                # Display in minutes for sub-hour reminders
                minutes = int(hours_before * 60)
                time_desc = f"{minutes} daqiqa"

            message = (
                f"🔔 <b>Tadbir eslatmasi!</b>\n\n"
                f"<b>{event['title']}</b>\n\n"
                f"📅 Sana: {event['date']}\n"
                f"🕐 Vaqt: {event['time']}\n"
                f"📍 Joy: {event['place']}\n"
                f"💬 Izoh: {event.get('comment', 'Izoh yoʼq')}\n\n"
                f"👤 Mas'ul: {event['creator_name']}\n"
                f"🏢 Bo'lim: {event['creator_department']}\n"
                f"📱 Telefon: {event['creator_phone']}\n\n"
                f"⏰ <b>{time_desc}</b> qoldi!"
            )

            await self.bot.send_message(
                chat_id=config.MEDIA_GROUP_CHAT_ID,
                text=message,
                parse_mode="HTML"
            )

        except Exception as e:
            print(f"❌ Error sending reminder: {e}")

    async def send_immediate_notification(self, event: dict):
        """Send immediate notification about new event to media group."""
        try:
            if not config.MEDIA_GROUP_CHAT_ID:
                return

            message = (
                f"📢 <b>Yangi tadbir qo'shildi!</b>\n\n"
                f"<b>{event['title']}</b>\n\n"
                f"📅 Sana: {event['date']}\n"
                f"🕐 Vaqt: {event['time']}\n"
                f"📍 Joy: {event['place']}\n"
                f"💬 Izoh: {event.get('comment', 'Izoh yoʼq')}\n\n"
                f"👤 Mas'ul: {event['creator_name']}\n"
                f"🏢 Bo'lim: {event['creator_department']}\n"
                f"📱 Telefon: {event['creator_phone']}"
            )

            await self.bot.send_message(
                chat_id=config.MEDIA_GROUP_CHAT_ID,
                text=message,
                parse_mode="HTML"
            )

        except Exception as e:
            print(f"❌ Error sending immediate notification: {e}")

    async def mark_past_events_job(self):
        """Daily job to mark past events in Google Sheets with gray background."""
        try:
            if sheets_manager.is_connected():
                sheets_manager.mark_past_events()
        except Exception as e:
            print(f"❌ Error in mark_past_events_job: {e}")
