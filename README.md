# Event Organizer Bot

Universitet tadbirlari boshqaruvi uchun Telegram bot. Tadbirlarni qo'shish, tahrirlash, bekor qilish va avtomatik eslatmalar yuborish imkoniyatini beradi.

## Texnologiyalar

| Texnologiya | Versiya | Vazifasi |
|-------------|---------|----------|
| Python | 3.8+ | Asosiy dasturlash tili |
| aiogram | 3.13.1 | Telegram Bot API framework |
| SQLite | - | Ma'lumotlar bazasi |
| aiosqlite | 0.20.0 | Asinxron SQLite driver |
| gspread | 6.1.2 | Google Sheets API |
| APScheduler | 3.10.4 | Avtomatik eslatmalar |
| pytz | 2024.1 | Vaqt zonasi (Asia/Tashkent) |

## Loyiha tuzilishi

```
Event-Organizer-Bot/
├── bot.py                 # Asosiy fayl - botni ishga tushiradi
├── config.py              # Barcha sozlamalar (.env dan o'qiydi)
├── database.py            # SQLite bilan ishlash (users, events, reminders, departments)
├── keyboards.py           # Telegram tugmalar
├── states.py              # FSM holatlar (ro'yxatdan o'tish, tadbir qo'shish, tahrirlash)
├── google_sheets.py       # Google Sheets integratsiyasi
├── scheduler.py           # Eslatmalar scheduleri (1 daqiqada bir tekshiradi)
├── handlers/
│   ├── __init__.py
│   ├── start.py           # /start, ro'yxatdan o'tish
│   ├── events.py          # Tadbir qo'shish, ko'rish, tahrirlash, bekor qilish
│   └── admin.py           # Admin: statistika, bo'limlar boshqaruvi
├── requirements.txt       # Python kutubxonalar ro'yxati
├── .env                   # Environment o'zgaruvchilari (MAXFIY)
├── credentials.json       # Google API kaliti (MAXFIY)
└── database.db            # SQLite bazasi (avtomatik yaratiladi)
```

## Bot funksiyalari

### Oddiy foydalanuvchilar uchun:
- **Ro'yxatdan o'tish**: Ism, bo'lim, telefon raqami (faqat Telegram kontakt orqali)
- **Tadbir qo'shish**: Nom, sana (DD.MM.YYYY), vaqt (HH:MM), joy, izoh
- **Tadbirlar jadvali**: Bugungi, haftalik, oylik
- **Mening tadbirlarim**: O'z tadbirlarini ko'rish, tahrirlash, bekor qilish

### Admin foydalanuvchilar uchun:
- **Statistika**: Bo'limlar bo'yicha tadbirlar soni
- **Bo'limlar boshqaruvi**: Yangi bo'lim qo'shish, o'chirish

### Avtomatik funksiyalar:
- Yangi tadbir qo'shilganda media guruhga xabar
- Tadbir tahrirlanganda media guruhga xabar
- Tadbir bekor qilinganda media guruhga xabar
- Eslatmalar: 24 soat, 3 soat, 1 soat, 30 daqiqa, 10 daqiqa oldin
- Google Sheets ga avtomatik sinxronlash
- O'tgan tadbirlarni "Otgan tadbirlar" varag'iga ko'chirish

## Deployment qo'llanmasi

### 1-qadam: Serverga ulanish

```bash
ssh user@server_ip
```

### 2-qadam: Kerakli dasturlarni o'rnatish

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv git -y
```

### 3-qadam: Loyihani yuklab olish

```bash
cd /opt  # yoki boshqa joy
git clone https://github.com/your-repo/Event-Organizer-Bot.git
cd Event-Organizer-Bot
```

### 4-qadam: Virtual environment yaratish

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5-qadam: Environment faylini sozlash

`.env` faylini yarating:

```bash
nano .env
```

Quyidagi ma'lumotlarni kiriting:

```env
# Telegram Bot Token (@BotFather dan olinadi)
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
GOOGLE_SPREADSHEET_ID=1ABC...xyz

# Admin foydalanuvchilar (Telegram ID, vergul bilan ajratilgan)
ADMIN_USER_IDS=123456789,987654321

# Media guruh ID (minus bilan boshlanadi)
MEDIA_GROUP_CHAT_ID=-1001234567890

# Database
DATABASE_PATH=database.db

# Vaqt zonasi
TIMEZONE=Asia/Tashkent
```

### 6-qadam: Google Sheets API sozlash

1. [Google Cloud Console](https://console.cloud.google.com/) ga kiring
2. Yangi loyiha yarating
3. "APIs & Services" > "Enable APIs" > "Google Sheets API" va "Google Drive API" ni yoqing
4. "Credentials" > "Create Credentials" > "Service Account" yarating
5. Service account uchun JSON kalit yarating va yuklab oling
6. Faylni `credentials.json` nomi bilan loyiha papkasiga joylashtiring
7. Google Sheets yarating va service account email'ini (credentials.json ichidagi `client_email`) "Editor" sifatida qo'shing
8. Spreadsheet ID ni `.env` fayliga qo'shing

### 7-qadam: Botni sinab ko'rish

```bash
source venv/bin/activate
python bot.py
```

Agar xatosiz ishga tushsa, `Ctrl+C` bilan to'xtating.

### 8-qadam: Systemd service yaratish (avtomatik ishga tushirish)

Service faylini yarating:

```bash
sudo nano /etc/systemd/system/event-bot.service
```

Quyidagi matnni kiriting:

```ini
[Unit]
Description=Event Organizer Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/Event-Organizer-Bot
Environment=PATH=/opt/Event-Organizer-Bot/venv/bin
ExecStart=/opt/Event-Organizer-Bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Serviceni yoqish:

```bash
sudo systemctl daemon-reload
sudo systemctl enable event-bot
sudo systemctl start event-bot
```

### 9-qadam: Statusni tekshirish

```bash
# Service holati
sudo systemctl status event-bot

# Loglarni ko'rish
sudo journalctl -u event-bot -f

# So'nggi 100 qator log
sudo journalctl -u event-bot -n 100
```

## Muhim buyruqlar

```bash
# Botni qayta ishga tushirish
sudo systemctl restart event-bot

# Botni to'xtatish
sudo systemctl stop event-bot

# Botni ishga tushirish
sudo systemctl start event-bot

# Loglarni real-time ko'rish
sudo journalctl -u event-bot -f

# Virtual environment faollashtirish
cd /opt/Event-Organizer-Bot
source venv/bin/activate

# Kutubxonalarni yangilash
pip install -r requirements.txt --upgrade
```

## Ma'lumotlar bazasi

Bot SQLite ishlatadi. Jadvallar:

| Jadval | Tavsif |
|--------|--------|
| `users` | Foydalanuvchilar (telegram_id, full_name, department, phone, is_admin) |
| `events` | Tadbirlar (id, title, date, time, place, comment, created_by_user_id, is_cancelled) |
| `reminders` | Yuborilgan eslatmalar (event_id, reminder_type, sent_at) |
| `departments` | Bo'limlar ro'yxati (id, name, is_active) |

Ma'lumotlar bazasini ko'rish:

```bash
sqlite3 database.db
.tables
SELECT * FROM users;
SELECT * FROM events WHERE is_cancelled = 0;
.quit
```

## Google Sheets tuzilishi

Bot ikkita varaq yaratadi:

**"Tadbirlar" varag'i** - Kelgusi tadbirlar:
| ID | Tadbir nomi | Sana | Vaqt | Joy | Izoh | Bo'lim | Mas'ul | Telefon | Yaratilgan vaqt |

**"Otgan tadbirlar" varag'i** - O'tgan tadbirlar (kulrang fon bilan)

## Eslatmalar tizimi

Scheduler har 1 daqiqada tekshiradi va quyidagi vaqtlarda eslatma yuboradi:
- 24 soat oldin (1 kun)
- 3 soat oldin
- 1 soat oldin
- 30 daqiqa oldin
- 10 daqiqa oldin

Har bir eslatma bir marta yuboriladi (`reminders` jadvalida saqlanadi).

## Xavfsizlik

- `.env` va `credentials.json` fayllarini hech qachon git'ga push qilmang
- `ALLOWED_USER_IDS` ro'yxatida faqat ruxsat berilgan foydalanuvchilar bo'lsin
- `ADMIN_USER_IDS` da faqat ishonchli adminlar bo'lsin
- Telefon raqami faqat Telegram kontakt orqali qabul qilinadi (boshqa raqam yuborish mumkin emas)

## Muammolarni hal qilish

### Bot ishga tushmayapti

```bash
# Loglarni tekshiring
sudo journalctl -u event-bot -n 50

# .env faylini tekshiring
cat .env

# Token to'g'riligini tekshiring
curl https://api.telegram.org/bot<TOKEN>/getMe
```

### Google Sheets ishlamayapti

```bash
# credentials.json mavjudligini tekshiring
ls -la credentials.json

# Spreadsheet ID to'g'riligini tekshiring
grep GOOGLE_SPREADSHEET_ID .env
```

### Eslatmalar kelmayapti

```bash
# MEDIA_GROUP_CHAT_ID to'g'riligini tekshiring
grep MEDIA_GROUP_CHAT_ID .env

# Botning guruhda a'zo ekanligini tekshiring
# Bot guruhga qo'shilgan bo'lishi kerak
```

### Database xatosi

```bash
# Bazani zaxiralash
cp database.db database.db.backup

# Bazani qayta yaratish (barcha ma'lumotlar o'chadi!)
rm database.db
python bot.py  # Yangi baza yaratiladi
```

## Yangilash

```bash
cd /opt/Event-Organizer-Bot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart event-bot
```

## Kontakt

Muammolar yuzaga kelganda GitHub Issues orqali murojaat qiling.

---

**Diqqat**: Bot ishga tushirilgandan keyin scheduler avtomatik boshlanadi. Eslatmalar har daqiqada tekshiriladi va MEDIA_GROUP_CHAT_ID ga yuboriladi.
