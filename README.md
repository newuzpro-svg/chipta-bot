# Chipta kuzatuvchi bot

Telegram bot: qayerdan-qayerga va sanani tanlaysiz (aviabilet — uzairways.online,
yoki poezd bileti — eticket.railway.uz), agar hozir chipta bo'lmasa, bot har
`CHECK_INTERVAL_MINUTES` (standart: 12) daqiqada tekshirib turadi va chipta
paydo bo'lishi bilan sizga Telegramda xabar yuboradi. Bot chiptani sotib olmaydi
— faqat mavjudligi haqida ogohlantiradi, xarid qilish uchun havola yuboradi.

## Ishga tushirish

```
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m playwright install chromium
.venv\Scripts\python bot.py
```

`.env` faylida bot tokeni allaqachon qo'yilgan (`BOT_TOKEN`). Uni hech kimga
bermang va reponi ochiq joyga (GitHub va h.k.) yuklasangiz `.env`ni
commit qilmang (`.gitignore`da allaqachon istisno qilingan).

## Qanday ishlaydi

- **Aviabilet**: `api.aerotur.aero` (uzairways.online saytining haqiqiy qidiruv
  backendi) ga to'g'ridan-to'g'ri so'rov yuboradi — tez va yengil.
- **Poezd bilet**: `eticket.railway.uz` bot himoyasi (WAF) oddiy HTTP
  so'rovlarni bloklaydi, shuning uchun bu qism headless brauzer (Playwright +
  Chromium) orqali haqiqiy foydalanuvchidek qidiruvni bajaradi va natijani
  saytning o'z API javobidan o'qiydi. Shu sababli poezd tekshiruvi biroz
  sekinroq va resursni ko'proq talab qiladi (bitta tekshiruv ~10-15 soniya,
  brauzer ochib-yopadi).
- Agar sayt to'g'ridan-to'g'ri ulanishni bloklasa (403/429/503 yoki tarmoq
  xatosi), bot ochiq (bepul) proxy-lar ro'yxatidan ishlaydigan birini topib,
  so'rovni shu orqali qayta yuboradi (`PROXY_ENABLED=true`). Bepul proxylar
  ko'pincha sekin yoki ishlamay qolishi mumkin — bu faqat zaxira variant.

## Render'ga bepul joylash

1. Repo GitHub'da (`newuzpro-svg/chipta-bot` yoki shunga o'xshash).
2. [render.com](https://render.com) da GitHub akkountingiz bilan ro'yxatdan o'ting.
3. Dashboard → **New** → **Blueprint** → shu repo'ni tanlang (`render.yaml` avtomatik topiladi) — yoki **New** → **Web Service** → repo'ni tanlang, **Environment: Docker** ni tanlang (Dockerfile avtomatik ishlatiladi).
4. **Environment Variables** bo'limida `BOT_TOKEN` qiymatini qo'lda kiriting (bu maxfiy, `.env`dan olib, git'ga tushmagan).
5. **Free** plan tanlanganligiga ishonch hosil qiling, Deploy bosing.
6. Bepul Render web-servisi 15 daqiqa harakatsizlikdan keyin uxlab qoladi — bot esa fonda ishlab turishi (chiptalarni tekshirishi) kerak. Shuning uchun tashqi bepul "ping" xizmati kerak: [cron-job.org](https://cron-job.org) yoki [UptimeRobot](https://uptimerobot.com) da ro'yxatdan o'tib, Render bergan URL manzilingizga (masalan `https://chipta-bot.onrender.com`) har 10 daqiqada so'rov yuborishni sozlang — shunda servis doim uyg'oq turadi.

Eslatma: Render bepul tarifida disk vaqtinchalik — har yangi deploy'da `data/subscriptions.db` (faol kuzatuvlar) tozalanadi, oddiy qayta ishga tushishda (sleep/wake) esa saqlanadi.

## Cheklovlar

- Aviabilet va poezd shaharlari/stansiyalari ro'yxati saytlarning o'zidan
  tasdiqlangan eng mashhur yo'nalishlar bilan cheklangan (`ticketbot/cities.py`).
  Boshqa yo'nalish kerak bo'lsa, shu faylga qo'shish kifoya.
- Poezd sayti ketma-ket ko'p qidiruvni vaqtincha bloklashi mumkin ("Foydalanuvchi
  vaqtinchalik bloklangan" xabari) — shuning uchun tekshiruvlar orasida
  kutish vaqtini juda qisqartirmang.
