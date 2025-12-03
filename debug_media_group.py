"""Debug script to test media group notifications."""
import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import config after loading env
import config

print("=" * 50)
print("🔍 MEDIA GROUP CONFIGURATION CHECK")
print("=" * 50)

print(f"\n1. .env file check:")
print(f"   MEDIA_GROUP_CHAT_ID (raw): {os.getenv('MEDIA_GROUP_CHAT_ID')}")

print(f"\n2. Config module check:")
print(f"   MEDIA_GROUP_CHAT_ID: {config.MEDIA_GROUP_CHAT_ID}")
print(f"   Type: {type(config.MEDIA_GROUP_CHAT_ID)}")

if config.MEDIA_GROUP_CHAT_ID:
    print(f"   ✅ Chat ID is configured correctly")
    print(f"   Chat ID: {config.MEDIA_GROUP_CHAT_ID}")
else:
    print(f"   ❌ ERROR: Chat ID is NOT configured!")
    print(f"\n   Fix:")
    print(f"   1. Open .env file")
    print(f"   2. Add: MEDIA_GROUP_CHAT_ID=-1001234567890")
    print(f"   3. Use YOUR group chat ID (negative number)")

print(f"\n3. Bot token check:")
if config.BOT_TOKEN:
    print(f"   ✅ Bot token is configured")
else:
    print(f"   ❌ ERROR: Bot token is NOT configured!")

print("\n" + "=" * 50)

# Test sending message (if configured)
async def test_send_message():
    """Test sending a message to the group."""
    if not config.MEDIA_GROUP_CHAT_ID or not config.BOT_TOKEN:
        print("❌ Cannot test sending - configuration incomplete")
        return

    try:
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode

        bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

        print("\n4. Testing message send...")
        print(f"   Sending to: {config.MEDIA_GROUP_CHAT_ID}")

        await bot.send_message(
            chat_id=config.MEDIA_GROUP_CHAT_ID,
            text="🧪 <b>Test xabari!</b>\n\nAgar bu xabarni ko'rayotgan bo'lsangiz, bot to'g'ri sozlangan! ✅",
            parse_mode="HTML"
        )

        print(f"   ✅ Message sent successfully!")
        print(f"   Check your Telegram group for the test message.")

        await bot.session.close()

    except Exception as e:
        print(f"   ❌ ERROR sending message: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_send_message())
