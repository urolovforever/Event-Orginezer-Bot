"""Main bot file for Event Organizer Bot."""
import asyncio
import logging
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import config
from database import db
from google_sheets import sheets_manager
from scheduler import ReminderScheduler
from handlers import start, events, admin


# Custom logging formatter with Tashkent timezone
class TashkentFormatter(logging.Formatter):
    """Logging Formatter that uses Tashkent timezone."""

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        self.tz = pytz.timezone(config.TIMEZONE)

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, self.tz)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime('%Y-%m-%d %H:%M:%S')


# Configure logging with Tashkent timezone
handler = logging.StreamHandler()
handler.setFormatter(TashkentFormatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
logging.basicConfig(
    level=logging.INFO,
    handlers=[handler]
)
logger = logging.getLogger(__name__)

# Global scheduler instance (needed in events.py)
reminder_scheduler = None


async def on_startup(bot: Bot):
    """Actions to perform on bot startup."""
    logger.info("Starting Event Organizer Bot...")

    # Initialize database
    await db.init_db()
    logger.info("Database initialized")

    # Initialize Google Sheets
    try:
        sheets_manager.initialize()
        if sheets_manager.is_connected():
            logger.info("Google Sheets connected successfully")
        else:
            logger.warning("Google Sheets not configured or connection failed")
    except Exception as e:
        logger.error(f"Error initializing Google Sheets: {e}")

    # Start reminder scheduler
    global reminder_scheduler
    reminder_scheduler = ReminderScheduler(bot)
    reminder_scheduler.start()

    # Set scheduler in events handler module
    from handlers import events as events_handler
    events_handler.reminder_scheduler = reminder_scheduler

    # Mark past events in Google Sheets with gray background
    if sheets_manager.is_connected():
        try:
            sheets_manager.mark_past_events()
            logger.info("Marked past events in Google Sheets")
        except Exception as e:
            logger.error(f"Error marking past events: {e}")

    logger.info("Bot startup complete!")


async def on_shutdown():
    """Actions to perform on bot shutdown."""
    logger.info("Shutting down Event Organizer Bot...")

    # Stop scheduler
    if reminder_scheduler:
        reminder_scheduler.stop()

    logger.info("Bot shutdown complete!")


async def main():
    """Main function to run the bot."""
    # Initialize bot and dispatcher
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())

    # Register routers
    dp.include_router(start.group_router)  # Group handler first (removes keyboards)
    dp.include_router(start.router)
    dp.include_router(events.router)
    dp.include_router(admin.router)

    # Register startup and shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Start polling
    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
