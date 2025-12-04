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
        """
        Start the scheduler with two jobs:
        1. Check reminders every 1 minute
        2. Mark past events daily at 00:05 AM
        """
        if not self.running:
            # Job 1: Check for reminders every 1 minute
            # Checks if it's time to send 24h, 3h, or 1h reminders
            self.scheduler.add_job(
                self.check_reminders,
                trigger=IntervalTrigger(minutes=1),
                id='check_reminders',
                replace_existing=True
            )
            print("✅ Reminder check job added (every 1 minute)")

            # Job 2: Mark past events daily at 00:05 (5 minutes after midnight)
            # Updates Google Sheets to color past events gray
            self.scheduler.add_job(
                self.mark_past_events_job,
                trigger=CronTrigger(hour=0, minute=5),
                id='mark_past_events',
                replace_existing=True
            )
            print("✅ Mark past events job added (daily at 00:05)")

            self.scheduler.start()
            self.running = True
            print("🚀 Reminder scheduler started successfully")

    def stop(self):
        """Stop the scheduler."""
        if self.running:
            self.scheduler.shutdown()
            self.running = False
            print("Reminder scheduler stopped")

    async def check_reminders(self):
        """
        Check for upcoming events and send reminders.

        This function runs every 1 minute and:
        1. Gets all upcoming (non-cancelled, future) events from database
        2. For each event, checks if it's time to send 24h, 3h, or 1h reminder
        3. Sends reminder if within time window and not already sent
        """
        try:
            now = datetime.now(pytz.timezone(config.TIMEZONE))
            events = await db.get_upcoming_events()

            print(f"🔍 Checking reminders at {now.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📋 Found {len(events)} upcoming events")

            # Check each event for reminder opportunities
            for event in events:
                await self._check_event_reminders(event, now)

        except Exception as e:
            print(f"❌ Error checking reminders: {e}")
            import traceback
            traceback.print_exc()

    async def _check_event_reminders(self, event: dict, now: datetime):
        """
        Check and send reminders for a specific event.

        Reminder logic:
        1. Event must not have started yet (event_datetime > now)
        2. For each reminder time (24h, 3h, 1h before):
           - If reminder time has passed OR is within next 60 minutes
           - AND reminder hasn't been sent yet
           - THEN send the reminder

        Why 60-minute window?
        - If reminder time was 13:00 and bot was offline
        - When bot comes back online at 13:30
        - We still send the reminder (because time_diff = -30 min <= 60 min)
        - This prevents missing reminders due to downtime

        Args:
            event: Event dictionary with id, title, date, time, etc.
            now: Current datetime in Tashkent timezone
        """
        try:
            # Step 1: Parse event date and time
            event_datetime = self._parse_event_datetime(event['date'], event['time'])
            if not event_datetime:
                print(f"⚠️ Could not parse datetime for event {event.get('id', 'unknown')}: {event.get('date')} {event.get('time')}")
                return

            print(f"📅 Checking event '{event.get('title', 'Unknown')}' scheduled for {event_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

            # Step 2: Check if event hasn't started yet
            event_time_diff = (event_datetime - now).total_seconds()

            if event_time_diff <= 0:
                print(f"  ⏭️ Event has already started or passed, skipping all reminders")
                return

            # Step 3: Check each reminder time (24h, 3h, 1h before event)
            for hours_before in config.REMINDER_HOURS:
                # Calculate when reminder should be sent
                reminder_time = event_datetime - timedelta(hours=hours_before)
                reminder_type = f"{hours_before}h_before"

                # Calculate time difference between now and reminder time
                time_diff = (reminder_time - now).total_seconds()
                time_diff_minutes = time_diff / 60

                print(f"  ⏰ {hours_before}h reminder: {time_diff_minutes:.1f} minutes until reminder time")

                # Step 4: Decide whether to send reminder
                # Send if:
                # - time_diff <= 3600 (reminder time is within next 60 minutes or has passed)
                # - Reminder hasn't been sent yet (checked in database)
                if time_diff <= 3600:  # 3600 seconds = 60 minutes
                    # Check if this reminder was already sent
                    already_sent = await db.is_reminder_sent(event['id'], reminder_type)

                    if not already_sent:
                        print(f"  📤 Sending {hours_before}h reminder for event {event['id']}")
                        await self._send_reminder(event, hours_before)
                        # Mark as sent in database to prevent duplicates
                        await db.add_reminder(event['id'], reminder_type)
                    else:
                        print(f"  ✓ {hours_before}h reminder already sent")
                else:
                    # Reminder time is too far in the future
                    print(f"  ⏸️ {hours_before}h reminder not yet due ({time_diff_minutes:.1f} min away)")

        except Exception as e:
            print(f"❌ Error checking event reminders: {e}")
            import traceback
            traceback.print_exc()

    def _parse_event_datetime(self, date_str: str, time_str: str) -> Optional[datetime]:
        """
        Parse event date and time strings into timezone-aware datetime object.

        Args:
            date_str: Date in DD.MM.YYYY format (e.g., "25.12.2024")
            time_str: Time in HH:MM format (e.g., "14:30")

        Returns:
            datetime: Timezone-aware datetime object in Tashkent timezone
            None: If parsing fails

        Example:
            >>> _parse_event_datetime("25.12.2024", "14:30")
            datetime(2024, 12, 25, 14, 30, tzinfo=<DstTzInfo 'Asia/Tashkent'>)
        """
        try:
            # Parse date (DD.MM.YYYY format)
            day, month, year = map(int, date_str.split('.'))

            # Parse time (HH:MM format, 24-hour)
            hour, minute = map(int, time_str.split(':'))

            # Create timezone-aware datetime object
            # Using Asia/Tashkent timezone from config
            event_datetime = datetime(
                year, month, day, hour, minute,
                tzinfo=pytz.timezone(config.TIMEZONE)
            )

            return event_datetime

        except Exception as e:
            print(f"❌ Error parsing event datetime '{date_str} {time_str}': {e}")
            return None

    async def _send_reminder(self, event: dict, hours_before: int):
        """
        Send reminder message to media group chat.

        Args:
            event: Event dictionary containing title, date, time, place, etc.
            hours_before: How many hours before event (24, 3, or 1)

        Message format:
            🔔 Tadbir eslatmasi!

            [Event title]

            📅 Sana: [date]
            🕐 Vaqt: [time]
            📍 Joy: [place]
            💬 Izoh: [comment]

            👤 Mas'ul: [creator name]
            🏢 Bo'lim: [department]
            📱 Telefon: [phone]

            ⏰ [time_left] qoldi!
        """
        try:
            if not config.MEDIA_GROUP_CHAT_ID:
                print("❌ Error: MEDIA_GROUP_CHAT_ID not configured in .env file")
                return

            print(f"📤 Sending {hours_before}h reminder to chat_id: {config.MEDIA_GROUP_CHAT_ID}")

            # Format time description in Uzbek
            if hours_before == 72:
                time_desc = "3 kun"
            elif hours_before == 24:
                time_desc = "1 kun"
            else:
                time_desc = f"{hours_before} soat"

            # Build reminder message with event details
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

            # Send to media group
            await self.bot.send_message(
                chat_id=config.MEDIA_GROUP_CHAT_ID,
                text=message,
                parse_mode="HTML"
            )

            print(f"✅ Reminder sent successfully for event {event['id']} ({hours_before}h before)")

        except Exception as e:
            print(f"❌ Error sending reminder: {e}")
            import traceback
            traceback.print_exc()

    async def send_immediate_notification(self, event: dict):
        """
        Send immediate notification about new event to media group.

        This is called when a new event is created to inform all group members.

        Args:
            event: Event dictionary containing all event details

        Message format:
            📢 Yangi tadbir qo'shildi!

            [Event title]

            📅 Sana: [date]
            🕐 Vaqt: [time]
            📍 Joy: [place]
            💬 Izoh: [comment]

            👤 Mas'ul: [creator name]
            🏢 Bo'lim: [department]
            📱 Telefon: [phone]
        """
        try:
            if not config.MEDIA_GROUP_CHAT_ID:
                print("❌ Error: MEDIA_GROUP_CHAT_ID not configured in .env file")
                return

            print(f"📤 Sending immediate notification to chat_id: {config.MEDIA_GROUP_CHAT_ID}")

            # Build notification message
            message = (
                f"📢 <b>Yangi tadbir qo'shildi!</b>\n\n"
                f"<b>{event['title']}</b>\n\n"
                f"📅 Sana: {event['date']}\n"
                f"🕐 Vaqt: {event['time']}\n"
                f"📍 Joy: {event['place']}\n"
                f"💬 Izoh: {event.get('comment', 'Izoh yo'q')}\n\n"
                f"👤 Mas'ul: {event['creator_name']}\n"
                f"🏢 Bo'lim: {event['creator_department']}\n"
                f"📱 Telefon: {event['creator_phone']}"
            )

            # Send to media group
            await self.bot.send_message(
                chat_id=config.MEDIA_GROUP_CHAT_ID,
                text=message,
                parse_mode="HTML"
            )

            print(f"✅ Immediate notification sent successfully for event {event['id']}")

        except Exception as e:
            print(f"❌ Error sending immediate notification: {e}")
            import traceback
            traceback.print_exc()

    async def mark_past_events_job(self):
        """
        Daily job to mark past events in Google Sheets with gray background.

        Runs daily at 00:05 AM (Tashkent time) to:
        1. Check all events in Google Sheets
        2. Mark events with datetime < now as past (GRAY background)
        3. Keep cancelled events RED (skip them)
        4. Keep future events WHITE (no background)

        This ensures the sheet always has up-to-date color coding.
        """
        try:
            print("🔍 Running daily task: marking past events in Google Sheets")

            if sheets_manager.is_connected():
                sheets_manager.mark_past_events()
                print("✅ Past events marked successfully")
            else:
                print("⚠️ Google Sheets not connected, skipping mark past events")

        except Exception as e:
            print(f"❌ Error in mark_past_events_job: {e}")
            import traceback
            traceback.print_exc()
