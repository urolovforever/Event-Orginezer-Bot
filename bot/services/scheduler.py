import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from bot.database.db import db
from bot.config import Config

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """
    Scheduler for sending automatic reminders to the photographer.
    Uses APScheduler for reliable job scheduling.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.photographer_id = Config.PHOTOGRAPHER_ID

    def start(self):
        """
        Start the scheduler and register all jobs.
        """
        # Daily digest at 8:00 AM
        self.scheduler.add_job(
            self.send_daily_digest,
            CronTrigger(hour=8, minute=0),
            id="daily_digest",
            name="Send daily event digest to photographer"
        )

        # Check for 24-hour reminders every hour
        self.scheduler.add_job(
            self.send_24hour_reminders,
            IntervalTrigger(hours=1),
            id="24hour_reminders",
            name="Send 24-hour event reminders"
        )

        # Check for 1-hour reminders every 15 minutes
        self.scheduler.add_job(
            self.send_1hour_reminders,
            IntervalTrigger(minutes=15),
            id="1hour_reminders",
            name="Send 1-hour event reminders"
        )

        self.scheduler.start()
        logger.info("✅ Reminder scheduler started successfully")

    def stop(self):
        """Stop the scheduler gracefully"""
        self.scheduler.shutdown()
        logger.info("🛑 Reminder scheduler stopped")

    async def send_daily_digest(self):
        """
        Send daily digest of today's events to photographer.
        Runs every day at 8:00 AM.
        """
        try:
            logger.info("📧 Sending daily digest to photographer...")

            events = await db.get_events_today()

            if not events:
                message = (
                    "📅 **Daily Event Digest**\n\n"
                    "No events scheduled for today."
                )
            else:
                message = (
                    f"📅 **Daily Event Digest**\n\n"
                    f"You have {len(events)} event(s) today:\n\n"
                )

                for event in events:
                    message += (
                        f"📸 **{event.title}**\n"
                        f"   🕐 Time: {event.time}\n"
                        f"   📍 Location: {event.location}\n\n"
                    )

            await self.bot.send_message(
                chat_id=self.photographer_id,
                text=message,
                parse_mode="Markdown"
            )

            logger.info(f"✅ Daily digest sent ({len(events) if events else 0} events)")

        except Exception as e:
            logger.error(f"❌ Error sending daily digest: {e}")

    async def send_24hour_reminders(self):
        """
        Send reminders for events happening in 24 hours.
        Runs every hour.
        """
        try:
            logger.info("🔍 Checking for 24-hour reminders...")

            # Get events happening in approximately 24 hours
            events = await db.get_events_for_reminders(hours=24)

            for event in events:
                message = (
                    f"📸 **24-Hour Event Reminder**\n\n"
                    f"**{event.title}**\n\n"
                    f"📆 Date: {event.date}\n"
                    f"🕐 Time: {event.time}\n"
                    f"📍 Location: {event.location}\n"
                )

                if event.description:
                    message += f"\n📝 Description:\n{event.description}"

                await self.bot.send_message(
                    chat_id=self.photographer_id,
                    text=message,
                    parse_mode="Markdown"
                )

                logger.info(f"✅ 24h reminder sent for event: {event.title}")

            if events:
                logger.info(f"📤 Sent {len(events)} 24-hour reminder(s)")

        except Exception as e:
            logger.error(f"❌ Error sending 24-hour reminders: {e}")

    async def send_1hour_reminders(self):
        """
        Send reminders for events happening in 1 hour.
        Runs every 15 minutes.
        """
        try:
            logger.info("🔍 Checking for 1-hour reminders...")

            # Get events happening in approximately 1 hour
            events = await db.get_events_for_reminders(hours=1)

            for event in events:
                message = (
                    f"📸 **1-Hour Event Reminder**\n\n"
                    f"⚠️ Event starting soon!\n\n"
                    f"**{event.title}**\n\n"
                    f"📆 Date: {event.date}\n"
                    f"🕐 Time: {event.time}\n"
                    f"📍 Location: {event.location}\n"
                )

                if event.description:
                    message += f"\n📝 Description:\n{event.description}"

                await self.bot.send_message(
                    chat_id=self.photographer_id,
                    text=message,
                    parse_mode="Markdown"
                )

                logger.info(f"✅ 1h reminder sent for event: {event.title}")

            if events:
                logger.info(f"📤 Sent {len(events)} 1-hour reminder(s)")

        except Exception as e:
            logger.error(f"❌ Error sending 1-hour reminders: {e}")

    async def send_test_reminder(self):
        """
        Send a test reminder to verify scheduler is working.
        Can be called manually for testing.
        """
        try:
            message = (
                "🧪 **Test Reminder**\n\n"
                "This is a test message from the event reminder system.\n"
                "If you received this, the scheduler is working correctly!"
            )

            await self.bot.send_message(
                chat_id=self.photographer_id,
                text=message,
                parse_mode="Markdown"
            )

            logger.info("✅ Test reminder sent successfully")

        except Exception as e:
            logger.error(f"❌ Error sending test reminder: {e}")