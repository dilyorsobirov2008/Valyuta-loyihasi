import asyncio
import logging
import os
from datetime import datetime
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- SOZLAMALAR ---
# Token va ID-ni to'g'ridan-to'g'ri joylashtirdim
TOKEN = "8588087982:AAGpoXDGFhwrDGKLZ8WYJQXvlMMO8E7M8b8"
CHANNEL_ID = "-1003346733347"

bot = Bot(token=TOKEN)
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
                    # USD, EUR va RUB kurslarini ajratib olish
                    rates = {item['Ccy']: item['Rate'] for item in data if item['Ccy'] in ['USD', 'EUR', 'RUB']}
                    return rates
    except Exception as e:
        logging.error(f"API xatoligi: {e}")
    return None

# --- XABAR MATNINI TAYYORLASH ---
async def prepare_currency_text():
    rates = await get_exchange_rates()
    if rates:
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        text = (
            f"📊 <b>Bugungi valyuta kurslari</b>\n\n"
            f"💵 <b>USD:</b> {rates.get('USD')} so‘m\n"
            f"💶 <b>EUR:</b> {rates.get('EUR')} so‘m\n"
            f"🇷🇺 <b>RUB:</b> {rates.get('RUB')} so‘m\n\n"
            f"⏰ <b>Sana:</b> {current_time}"
        )
        return text
    return "⚠️ Kurslarni yuklashda muammo bo'ldi."

# --- KANALGA YUBORISH (KUNLIK) ---
async def send_daily_report():
    text = await prepare_currency_text()
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode=ParseMode.HTML)
        logging.info("Kunlik hisobot yuborildi.")
    except Exception as e:
        logging.error(f"Xatolik: {e}")

# --- YANGI A'ZO KIRGANDA YUBORISH ---
@dp.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_user_join(event: types.ChatMemberUpdated):
    if str(event.chat.id) == str(CHANNEL_ID):
        text = await prepare_currency_text()
        try:
            await bot.send_message(
                chat_id=CHANNEL_ID, 
                text=f"🌟 <b>Yangi a'zo qo'shildi!</b>\n\n{text}", 
                parse_mode=ParseMode.HTML
            )
            logging.info("Yangi a'zoga kurs yuborildi.")
        except Exception as e:
            logging.error(f"Xatolik: {e}")

# --- ASOSIY ISHGA TUSHIRISH ---
async def main():
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    
    # Har kuni soat 09:00 da avtomatik yuborish
    scheduler.add_job(send_daily_report, "cron", hour=9, minute=0)
    scheduler.start()

    logging.info("Bot ishga tushdi...")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")