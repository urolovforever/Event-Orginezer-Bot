"""Configuration module for the Event Organizer Bot."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables")

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
GOOGLE_SPREADSHEET_ID = os.getenv('GOOGLE_SPREADSHEET_ID')

# Admin Configuration
ADMIN_USER_IDS = [
    int(user_id.strip())
    for user_id in os.getenv('ADMIN_USER_IDS', '').split(',')
    if user_id.strip().isdigit()
]

# Media group chat ID (convert to int)
MEDIA_GROUP_CHAT_ID_STR = os.getenv('MEDIA_GROUP_CHAT_ID', '')
MEDIA_GROUP_CHAT_ID = int(MEDIA_GROUP_CHAT_ID_STR) if MEDIA_GROUP_CHAT_ID_STR and MEDIA_GROUP_CHAT_ID_STR.lstrip('-').isdigit() else None

# Database Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'database.db')

# Timezone
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Tashkent')

# Departments list (predefined)
DEPARTMENTS = [
    "Rektorat",
    "O'quv bo'limi",
    "Ilmiy bo'lim",
    "Marketing",
    "Media markazi",
    "Talabalar turar joyi",
    "Axborot texnologiyalari",
    "Kadrlar bo'limi",
    "Buxgalteriya",
    "Xorijiy talabalar bo'limi",
    "Boshqa"
]

# Reminder settings (in hours before event)
REMINDER_HOURS = [24, 3, 1]  # 1 day, 3 hours, and 1 hour before event
