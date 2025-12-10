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
# config.py
ALLOWED_USER_IDS = [
    632450666,
    1194431231,
    1457627,
    57315040,
    920210298,
    690810839,
    293706763,
    8423839879,
    7299003750,
    360028026,
    120623157,
    1754943160,
    6097246027,
    217758062,
    364276541,
    679412106,
    7955458633,
    1439467922,
    1028998997,
    180372444,
    5688383240,
    1946925,
    6132056977,
    1237697541,
    2059962338,
    1979650569,
    1862325066,
    541179627,
    2182965,
    110118230,
    5636043125,
    52950202,
    44459289,
    1920079641,
    350117641,
    497251343,
    1232718829,
    247090639,
    7659680544,
    5573136938

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
    "Yurisprudensiya fakulteti",
    "Biznes va innovatsion ta'lim fakulteti",
    "Huquqiy fanlar kafedrasi",
    "Aniq fanlar va raqamli texnalogiyalar fakulteti",
    "Ijtimoiy fanlar va ta'lim kafedrasi",
    "Xorijiy tillar kafedrasi",
    "Yoshlar bilan ishlash departamenti",
    "Akademik ishlar departamenti",
    "Innovatsion ta'lim va iqtidorli talabalar bilan ishlash",
    "Ilmiy tadqiqotlar va innovatsiyalar departamenti",
    "HR departamenti",
    "Xalqaro aloqalar departamenti",
    "Registrator offis",
    "IT departamenti",
    "Ta'lim sifati va imtihonlarni nazorat qilish departamenti",
    "Axborot-resurs markazi"
]

# Reminder settings (in hours before event)
# Supports fractional hours: 0.5 = 30 minutes, 0.1667 = 10 minutes
REMINDER_HOURS = [24, 3, 1, 0.5, 0.1667]  # 1 day, 3 hours, 1 hour, 30 minutes, and 10 minutes before event
