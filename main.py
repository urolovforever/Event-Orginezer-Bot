import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import Config
from bot.database.db import db
from bot.handlers import common, user, admin
from bot.middlewares.admin import AdminMiddleware
from bot.services.scheduler import ReminderScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log")
    ]
)

logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """
    Actions to perform on bot startup.
    """
    logger.info("🚀 Starting University Event Bot...")

    # Initialize database
    await db.init_db()
    logger.info("✅ Database initialized")

    # Send startup notification to photographer
    try:
        await bot.send_message(
            chat_id=Config.PHOTOGRAPHER_ID,
            text="🤖 Event Bot is now online and ready!"
        )
        logger.info("✅ Startup notification sent to photographer")
    except Exception as e:
        logger.warning(f"⚠️ Could not send startup notification: {e}")

    logger.info("✅ Bot started successfully")


async def on_shutdown(bot: Bot, scheduler: ReminderScheduler):
    """
    Actions to perform on bot shutdown.
    """
    logger.info("🛑 Shutting down bot...")

    # Stop scheduler
    scheduler.stop()

    # Send shutdown notification
    try:
        await bot.send_message(
            chat_id=Config.PHOTOGRAPHER_ID,
            text="🤖 Event Bot is going offline."
        )
        logger.info("✅ Shutdown notification sent")
    except Exception as e:
        logger.warning(f"⚠️ Could not send shutdown notification: {e}")

    logger.info("✅ Bot stopped successfully")


async def main():
    """
    Main function to run the bot.
    """
    try:
        # Validate configuration
        Config.validate()
        logger.info("✅ Configuration validated")

    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        logger.error("Please check your .env file and ensure all required values are set.")
        sys.exit(1)

    # Initialize bot and dispatcher
    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )

    dp = Dispatcher()

    # Register middlewares
    dp.message.middleware(AdminMiddleware())
    dp.callback_query.middleware(AdminMiddleware())
    logger.info("✅ Middlewares registered")

    # Register routers
    dp.include_router(common.router)
    dp.include_router(user.router)
    dp.include_router(admin.router)
    logger.info("✅ Routers registered")

    # Initialize reminder scheduler
    scheduler = ReminderScheduler(bot)
    scheduler.start()

    # Register startup handler
    dp.startup.register(on_startup)

    # Register shutdown handler
    async def shutdown_wrapper(bot: Bot):
        await on_shutdown(bot, scheduler)

    dp.shutdown.register(shutdown_wrapper)

    try:
        # Start polling
        logger.info("🔄 Starting polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

    except KeyboardInterrupt:
        logger.info("⌨️ Received keyboard interrupt")

    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise

    finally:
        await bot.session.close()
        logger.info("✅ Bot session closed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.critical(f"💥 Critical error: {e}")
        sys.exit(1)