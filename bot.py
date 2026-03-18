import os
import requests
import google.generativeai as genai
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIG ---
BOT_TOKEN = "8761244270:AAFGwkbkS9unmQgQ1ylc7hM3h6PE3NNkAog"
GEMINI_API_KEY = "AIzaSyAJw85B4keeWncASrOrkIdao7zZ40DPUYw"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- LOGIC ---
async def fetch_price(update: Update, symbol: str):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd&include_24hr_change=true"
    try:
        res = requests.get(url, timeout=15).json()
        if symbol.lower() in res:
            p, c = res[symbol.lower()]['usd'], res[symbol.lower()]['usd_24h_change']
            await update.message.reply_text(f"💰 {symbol.upper()}\nPrice: ${p:,}\n24h: {c:.2f}%")
        else:
            await update.message.reply_text("❌ Coin ရှာမတွေ့ပါ။")
    except:
        await update.message.reply_text("⚠️ API Error.")

async def ai_query(update: Update, text: str):
    try:
        response = model.generate_content(f"Answer in Burmese: {text}")
        await update.message.reply_text(response.text)
    except:
        await update.message.reply_text("AI Error.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ReplyKeyboardMarkup([[KeyboardButton("💰 BTC Price"), KeyboardButton("💰 ETH Price")]], resize_keyboard=True)
    await update.message.reply_text("Bot is Online! 🚀", reply_markup=kb)

# --- RUN ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), 
        lambda u, c: fetch_price(u, "bitcoin") if u.message.text == "💰 BTC Price" 
        else (fetch_price(u, "ethereum") if u.message.text == "💰 ETH Price" 
        else ai_query(u, u.message.text))))
    
    print("🚀 Bot is running on Koyeb...")
    app.run_polling()
