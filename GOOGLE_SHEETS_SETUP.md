# Google Sheets Sozlash Qo'llanmasi

## 1. Google Cloud Console'da loyiha yaratish

1. [Google Cloud Console](https://console.cloud.google.com/) ga kiring
2. Yangi loyiha yarating (masalan: "TIU-Event-Bot")
3. Loyihani tanlang

## 2. API'larni yoqish

1. Chap menyu: "APIs & Services" > "Enable APIs and Services"
2. Qidiruvda "Google Sheets API" ni toping va yoqing (Enable)
3. Qidiruvda "Google Drive API" ni toping va yoqing (Enable)

## 3. Service Account yaratish

1. "APIs & Services" > "Credentials"
2. "Create Credentials" > "Service Account"
3. Service account nomi: "event-bot-service"
4. "Create and Continue" tugmasini bosing
5. Role: "Editor" tanlang
6. "Continue" va "Done"

## 4. JSON kalit faylini yuklab olish

1. Yangi yaratilgan service account'ni tanlang
2. "Keys" tabiga o'ting
3. "Add Key" > "Create new key"
4. "JSON" ni tanlang va "Create"
5. Yuklab olingan JSON faylni `credentials.json` nomi bilan loyiha papkasiga joylashtiring

## 5. Google Sheets yaratish

1. [Google Sheets](https://sheets.google.com/) ga o'ting
2. Yangi spreadsheet yarating
3. Nom: "TIU Media Tadbirlar Jadvali" (yoki istalgan nom)
4. URL'dan Spreadsheet ID'ni oling:
   ```
   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
                                              ^^^^^^^^^^^
                                              Bu qism ID
   ```
5. ID'ni `.env` fayliga qo'shing:
   ```
   GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here
   ```

## 6. Service Account'ga ruxsat berish

**MUHIM:** Bu qadamni o'tkazib yubormaslik kerak!

1. Google Sheets faylini oching
2. "Share" (Ulashish) tugmasini bosing
3. `credentials.json` faylidagi `client_email` ni ko'chirib oling
   ```json
   {
     "client_email": "event-bot-service@your-project.iam.gserviceaccount.com"
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     Bu email'ni nusxalang
   }
   ```
4. Sheets'da "Share" oynasiga bu email'ni kiriting
5. Ruxsat: "Editor" (yoki "Viewer" faqat ko'rish uchun)
6. "Send" tugmasini bosing (email yuborishni o'chirish mumkin)

## 7. Botda sozlash

Bot avtomatik ravishda:
- "Tadbirlar" nomli sheet yaratadi (agar yo'q bo'lsa)
- Ustun sarlavhalarini o'rnatadi
- Har bir yangi tadbir qo'shilganda avtomatik yozadi

## Muammolarni hal qilish

### "Spreadsheet not found" xatosi
- Spreadsheet ID to'g'ri ekanligini tekshiring
- Service account email Sheets'ga qo'shilganligini tekshiring

### "Permission denied" xatosi
- Service account'ga "Editor" huquqi berilganligini tekshiring
- Google Sheets API va Google Drive API yoqilganligini tekshiring

### "credentials.json not found"
- Faylning loyiha papkasida ekanligini tekshiring
- Fayl nomi to'g'ri yozilganligini tekshiring (kichik harflar)

## Sheet tuzilishi

Bot quyidagi ustunlarni yaratadi:

| ID | Tadbir nomi | Sana | Vaqt | Joy | Izoh | Bo'lim | Mas'ul (F.I.Sh.) | Telefon | Yaratilgan vaqt |
|----|-------------|------|------|-----|------|--------|------------------|---------|-----------------|

Bekor qilingan tadbirlar qizil rangda belgilanadi va nomi boshiga "[BEKOR QILINDI]" qo'shiladi.
