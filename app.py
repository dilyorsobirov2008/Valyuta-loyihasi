import asyncio
import logging
import aiohttp
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- SOZLAMALAR ---
TOKEN = "8588087982:AAGpoXDGFhwrDGKLZ8WYJQXvlMMO8E7M8b8"
CHANNEL_ID = "-1003346733347"

# Botni sozlash
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# --- VALYUTA MA'LUMOTLARINI OLISH ---
async def get_exchange_rates():
    url = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    rates = {item['Ccy']: item['Rate'] for item in data if item['Ccy'] in ['USD', 'EUR', 'RUB']}
                    return rates
    except Exception as e:
        logging.error(f"API xatoligi: {e}")
    return None

# --- XABAR MATNINI TAYYORLASH ---
async def prepare_currency_text():
    rates = await get_exchange_rates()
    if rates:
        current_time = datetime.now().strftime("%d.%m.%Y")
        text = (
            f"📊 <b>Bugungi valyuta kurslari</b>\n"
            f"🗓 <i>Sana: {current_time}</i>\n\n"
            f"💵 <b>USD:</b> {rates.get('USD')} so‘m\n"
            f"💶 <b>EUR:</b> {rates.get('EUR')} so‘m\n"
            f"🇷🇺 <b>RUB:</b> {rates.get('RUB')} so‘m\n\n"
            f"📢 @kanalingiz_nomi" # Kanal silkasini yozib qo'yishingiz mumkin
        )
        return text
    return None

# --- KANALGA YUBORISH FUNKSIYASI ---
async def send_daily_report():
    text = await prepare_currency_text()
    if text:
        try:
            await bot.send_message(chat_id=CHANNEL_ID, text=text)
            logging.info("Ertalabki hisobot muvaffaqiyatli yuborildi.")
        except Exception as e:
            logging.error(f"Xabar yuborishda xatolik: {e}")

# --- ASOSIY ISHGA TUSHIRISH ---
async def main():
    # Scheduler (Rejalashtiruvchi) sozlamasi
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    
    # Har kuni soat 10:00 da ishga tushadi
    scheduler.add_job(send_daily_report, "cron", hour=10, minute=0)
    scheduler.start()

    logging.info("Bot ishga tushdi. Har kuni 10:00 da xabar yuboriladi.")
    
    try:
        # Faqat botni o'zini kutib turadi (Polling)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")