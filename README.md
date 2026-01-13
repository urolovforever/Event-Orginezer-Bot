# Event Organizer Bot 🎯

Bu bot universitet uchun tadbirlar boshqaruvi tizimi. Bot orqali tadbirlarni qo'shish, ko'rish, tahrirlash va bekor qilish mumkin. Shuningdek, media jamoasiga avtomatik eslatmalar yuboriladi.

## Xususiyatlar ✨

### 1️⃣ Foydalanuvchini ro'yxatdan o'tkazish
- Birinchi kirishda avtomatik ro'yxatdan o'tish jarayoni
- Ism-familiya, bo'lim va telefon raqamini to'plash
- Ma'lumotlar bazaga va Google Sheets ga saqlanadi

### 2️⃣ Tadbir qo'shish
- Tadbir nomi, sana, vaqt, joy va izohni kiritish
- Sana va vaqt validatsiyasi (DD.MM.YYYY va HH:MM formatida)
- Tasdiqlash oldin ko'rinish
- Avtomatik Google Sheets ga qo'shish
- Media guruhiga darhol xabar yuborish

### 3️⃣ Tadbirlar jadvali
- Bugungi tadbirlar
- Haftalik jadval
- Barcha kelgusi tadbirlar

### 4️⃣ Mening tadbirlarim
- O'zingiz qo'shgan tadbirlarni ko'rish
- Tadbirlarni tahrirlash
- Tadbirlarni bekor qilish

### 5️⃣ Admin panel
- Statistika (bo'limlar bo'yicha tadbirlar soni)
- Barcha foydalanuvchilarni ko'rish

### 6️⃣ Avtomatik eslatmalar
- Tadbirdan 24 soat oldin
- Tadbirdan 3 soat oldin
- Media guruhiga yuboriladi

### 7️⃣ Google Sheets integratsiyasi
- Barcha tadbirlar avtomatik Google Sheets ga yoziladi
- Media jamoasi real-time ko'rib boradi
- Tahrirlangan yoki bekor qilingan tadbirlar yangilanadi

## O'rnatish 🚀

### 1. Repository'ni klonlash

```bash
git clone https://github.com/your-username/Event-Organizer-Bot.git
cd Event-Organizer-Bot
```

### 2. Virtual environment yaratish

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
venv\Scripts\activate  # Windows
```

### 3. Kerakli kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

### 4. Environment o'zgaruvchilarini sozlash

`.env.example` faylini `.env` ga nusxalang va quyidagi ma'lumotlarni to'ldiring:

```env
BOT_TOKEN=your_telegram_bot_token_here
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here
ADMIN_USER_IDS=123456789,987654321
MEDIA_GROUP_CHAT_ID=-1001234567890
DATABASE_PATH=database.db
TIMEZONE=Asia/Tashkent
```

### 5. Google Sheets API sozlash

1. [Google Cloud Console](https://console.cloud.google.com/) ga kiring
2. Yangi loyiha yarating yoki mavjud loyihani tanlang
3. "APIs & Services" > "Enable APIs and Services" ga o'ting
4. "Google Sheets API" va "Google Drive API" ni yoqing
5. "Credentials" > "Create Credentials" > "Service Account" ni tanlang
6. Service account yarating va JSON kalit faylini yuklab oling
7. JSON faylni `credentials.json` nomi bilan loyiha papkasiga joylashtiring
8. Google Sheets faylini yarating
9. Service account email manzilini (credentials.json ichidagi `client_email`) Google Sheets fayliga "Editor" huquqi bilan qo'shing
10. Spreadsheet ID ni `.env` fayliga qo'shing (URL dan: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`)

### 6. Telegram bot yaratish

1. [@BotFather](https://t.me/BotFather) ga murojaat qiling
2. `/newbot` buyrug'ini yuboring
3. Bot nomini va username'ini kiriting
4. Olingan token'ni `.env` fayliga qo'shing

### 7. Admin va Media guruh sozlash

1. O'zingizning Telegram ID'ingizni oling ([@userinfobot](https://t.me/userinfobot) orqali)
2. ID'ni `ADMIN_USER_IDS` ga qo'shing
3. Media guruh yarating va botni qo'shing
4. Guruh ID'sini oling va `MEDIA_GROUP_CHAT_ID` ga qo'shing

**Guruh ID'sini olish:**
```bash
# Botni guruhga qo'shing va biror xabar yuboring
# Keyin quyidagi URL'ni brauzerda oching:
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
# "chat":{"id":-1001234567890 ko'rinishidagi ID'ni oling
```

### 8. Botni ishga tushirish

```bash
python bot.py
```

## Loyiha tuzilishi 📁

```
Event-Organizer-Bot/
├── bot.py                    # Asosiy bot fayli
├── config.py                 # Konfiguratsiya
├── database.py               # Ma'lumotlar bazasi
├── keyboards.py              # Keyboard layoutlar
├── states.py                 # FSM state'lari
├── google_sheets.py          # Google Sheets integratsiyasi
├── scheduler.py              # Eslatmalar scheduleri
├── handlers/
│   ├── __init__.py
│   ├── start.py             # Ro'yxatdan o'tish
│   ├── events.py            # Tadbirlar boshqaruvi
│   └── admin.py             # Admin funksiyalari
├── requirements.txt          # Python kutubxonalari
├── .env.example             # Environment o'zgaruvchilari namunasi
├── .env                     # Environment o'zgaruvchilari (gitignore)
├── credentials.json.example # Google credentials namunasi
├── credentials.json         # Google credentials (gitignore)
├── database.db              # SQLite database (gitignore)
└── README.md                # Bu fayl
```

## Foydalanish 📖

### Foydalanuvchi uchun

1. Botni `/start` buyrug'i bilan boshlang
2. Ro'yxatdan o'tish jarayonini yakunlang
3. Asosiy menyudan kerakli bo'limni tanlang:
   - ➕ Tadbir qo'shish
   - 📅 Tadbirlar jadvali
   - 📝 Mening tadbirlarim

### Admin uchun

Admin foydalanuvchilar qo'shimcha funksiyalarga ega:
- 📊 Statistika - bo'limlar bo'yicha tadbirlar soni
- 👥 Barcha foydalanuvchilar

## Texnologiyalar 🛠

- **Python 3.8+**
- **aiogram 3.13** - Telegram Bot API uchun asinxron framework
- **SQLite** - Mahalliy ma'lumotlar bazasi
- **Google Sheets API** - Google Sheets integratsiyasi
- **APScheduler** - Eslatmalar uchun scheduler
- **pytz** - Vaqt zonalari

## Muammolarni hal qilish 🔧

### Bot ishlamayapti

1. `.env` faylidagi barcha ma'lumotlar to'g'riligini tekshiring
2. `BOT_TOKEN` to'g'ri va aktiv ekanligini tekshiring
3. Virtual environment faollashtirilganligini tekshiring
4. Log'larni tekshiring: botni ishga tushirganda terminal'da xatolar ko'rinadi

### Google Sheets ishlamayapti

1. `credentials.json` fayli loyiha papkasida ekanligini tekshiring
2. Service account email'i Google Sheets fayliga qo'shilganligini tekshiring
3. Google Sheets API va Google Drive API yoqilganligini tekshiring
4. Spreadsheet ID to'g'ri ekanligini tekshiring

### Eslatmalar kelmayapti

1. `MEDIA_GROUP_CHAT_ID` to'g'ri ekanligini tekshiring
2. Bot guruhda admin yoki a'zo ekanligini tekshiring
3. Scheduler ishlab turganligini terminal log'laridan tekshiring

## Kelajakdagi rejalar 🎯

- [ ] Tadbirlarni tahrirlash funksiyasi
- [ ] Fayllar (rasm, video) yuklash imkoniyati
- [ ] Tadbirlar uchun ro'yxatga olish tizimi
- [ ] Excel export funksiyasi
- [ ] Multi-language support (O'zbek, Rus, Ingliz)
- [ ] Web panel admin uchun
- [ ] Mobil ilovalar (iOS/Android)

## Muallif ✍️

Bot **Claude Code** yordamida yaratildi.

## Litsenziya 📄

MIT License

## Yordam 🤝

Agar savollaringiz bo'lsa, issue ochishingiz yoki pull request yuborishingiz mumkin.

---

**Eslatma:** Bu bot universitet ichki ishlatilishi uchun yaratilgan. Ishlatishdan oldin barcha sozlamalarni to'g'ri amalga oshiring.