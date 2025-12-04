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
        """Start the scheduler."""
        if not self.running:
            # Check for reminders every 5 minutes
            self.scheduler.add_job(
                self.check_reminders,
                trigger=IntervalTrigger(minutes=5),
                id='check_reminders',
                replace_existing=True
            )

            # Reorganize events daily at 00:05 (5 minutes after midnight)
            self.scheduler.add_job(
                self.reorganize_events_job,
                trigger=CronTrigger(hour=0, minute=5),
                id='reorganize_events',
                replace_existing=True
            )

            self.scheduler.start()
            self.running = True
            print("Reminder scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if self.running:
            self.scheduler.shutdown()
            self.running = False
            print("Reminder scheduler stopped")

    async def check_reminders(self):
        """Check for upcoming events and send reminders."""
        try:
            now = datetime.now(pytz.timezone(config.TIMEZONE))
            events = await db.get_upcoming_events()

            print(f"🔍 Checking reminders at {now.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📋 Found {len(events)} upcoming events")

            for event in events:
                await self._check_event_reminders(event, now)

        except Exception as e:
            print(f"❌ Error checking reminders: {e}")
            import traceback
            traceback.print_exc()

    async def _check_event_reminders(self, event: dict, now: datetime):
        """Check and send reminders for a specific event."""
        try:
            # Parse event date and time
            event_datetime = self._parse_event_datetime(event['date'], event['time'])
            if not event_datetime:
                print(f"⚠️ Could not parse datetime for event {event.get('id', 'unknown')}: {event.get('date')} {event.get('time')}")
                return

            print(f"📅 Checking event '{event.get('title', 'Unknown')}' scheduled for {event_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

            # Check each reminder time
            for hours_before in config.REMINDER_HOURS:
                reminder_time = event_datetime - timedelta(hours=hours_before)
                reminder_type = f"{hours_before}h_before"

                # Check if it's time to send reminder
                time_diff = (reminder_time - now).total_seconds()
                time_diff_minutes = time_diff / 60

                print(f"  ⏰ {hours_before}h reminder: {time_diff_minutes:.1f} minutes until reminder time")

                # Send reminder if it's within the next 10 minutes and hasn't been sent
                # Window is 10 minutes to avoid missing reminders due to 5-minute check interval
                if 0 <= time_diff <= 600:  # 600 seconds = 10 minutes
                    if not await db.is_reminder_sent(event['id'], reminder_type):
                        print(f"  📤 Sending {hours_before}h reminder for event {event['id']}")
                        await self._send_reminder(event, hours_before)
                        await db.add_reminder(event['id'], reminder_type)
                    else:
                        print(f"  ✓ {hours_before}h reminder already sent")

        except Exception as e:
            print(f"❌ Error checking event reminders: {e}")
            import traceback
            traceback.print_exc()

    def _parse_event_datetime(self, date_str: str, time_str: str) -> Optional[datetime]:
        """Parse event date and time strings into datetime object."""
        try:
            # Parse date (DD.MM.YYYY)
            day, month, year = map(int, date_str.split('.'))

            # Parse time (HH:MM)
            hour, minute = map(int, time_str.split(':'))

            # Create datetime object with timezone
            event_datetime = datetime(
                year, month, day, hour, minute,
                tzinfo=pytz.timezone(config.TIMEZONE)
            )

            return event_datetime

        except Exception as e:
            print(f"Error parsing event datetime: {e}")
            return None

    async def _send_reminder(self, event: dict, hours_before: int):
        """Send reminder message to media group."""
        try:
            if not config.MEDIA_GROUP_CHAT_ID:
                print("❌ Error: MEDIA_GROUP_CHAT_ID not configured in .env file")
                return

            print(f"📤 Sending reminder to chat_id: {config.MEDIA_GROUP_CHAT_ID}")

            # Format time description
            if hours_before == 72:
                time_desc = "3 kun"
            elif hours_before == 24:
                time_desc = "1 kun"
            else:
                time_desc = f"{hours_before} soat"

            message = (
                f"🔔 <b>Tadbir eslatmasi!</b>\n\n"
                f"<b>{event['title']}</b>\n\n"
                f"📅 Sana: {event['date']}\n"
                f"🕐 Vaqt: {event['time']}\n"
                f"📍 Joy: {event['place']}\n"
                f"💬 Izoh: {event.get('comment', 'Izoh yo'q')}\n\n"
                f"👤 Mas'ul: {event['creator_name']}\n"
                f"🏢 Bo'lim: {event['creator_department']}\n"
                f"📱 Telefon: {event['creator_phone']}\n\n"
                f"⏰ Tadbirgacha {time_desc} qoldi!"
            )

            await self.bot.send_message(
                chat_id=config.MEDIA_GROUP_CHAT_ID,
                text=message,
                parse_mode="HTML"
            )

            print(f"✅ Reminder sent for event {event['id']} ({hours_before}h before)")

        except Exception as e:
            print(f"❌ Error sending reminder: {e}")
            import traceback
            traceback.print_exc()

    async def send_immediate_notification(self, event: dict):
        """Send immediate notification about new event to media group."""
        try:
            if not config.MEDIA_GROUP_CHAT_ID:
                print("❌ Error: MEDIA_GROUP_CHAT_ID not configured in .env file")
                return

            print(f"📤 Sending immediate notification to chat_id: {config.MEDIA_GROUP_CHAT_ID}")

            message = (
                f"📢 <b>Yangi tadbir qo'shildi!</b>\n\n"
                f"<b>{event['title']}</b>\n\n"
                f"📅 Sana: {event['date']}\n"
                f"🕐 Vaqt: {event['time']}\n"
                f"📍 Joy: {event['place']}\n"
                f"💬 Izoh: {event.get('comment', 'Izoh yo‘q')}\n\n"
                f"👤 Mas'ul: {event['creator_name']}\n"
                f"🏢 Bo'lim: {event['creator_department']}\n"
                f"📱 Telefon: {event['creator_phone']}"
            )

            await self.bot.send_message(
                chat_id=config.MEDIA_GROUP_CHAT_ID,
                text=message,
                parse_mode="HTML"
            )

            print(f"✅ Immediate notification sent for event {event['id']}")

        except Exception as e:
            print(f"❌ Error sending immediate notification: {e}")
            import traceback
            traceback.print_exc()

    async def reorganize_events_job(self):
        """Daily job to reorganize events in Google Sheets (future at top, past at bottom with gray background)."""
        try:
            print("🔍 Running daily task: reorganizing events in Google Sheets")
            if sheets_manager.is_connected():
                sheets_manager.reorganize_events()
                print("✅ Events reorganized successfully")
            else:
                print("⚠️ Google Sheets not connected, skipping reorganize events")
        except Exception as e:
            print(f"❌ Error in reorganize_events_job: {e}")
            import traceback
            traceback.print_exc()
