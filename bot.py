import requests
import google.generativeai as genai
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- CONFIGURATIONS (မင်းရဲ့ Key များ ပြောင်းထည့်ရန်) ---
BOT_TOKEN = "8761244270:AAFGwkbkS9unmQgQ1ylc7hM3h6PE3NNkAog"
GEMINI_API_KEY = "AIzaSyAJw85B4keeWncASrOrkIdao7zZ40DPUYw"
CHANNEL_ID = "@uniquetechteam" # @ ပါရပါမည်

# Gemini Setup
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Global Coin Database
COIN_MAP = {}

def refresh_coin_list():
    global COIN_MAP
    try:
        res = requests.get("https://api.coingecko.com/api/v3/coins/list").json()
        COIN_MAP = {coin['symbol'].lower(): coin['id'] for coin in res}
        print("✅ Coin database updated!")
    except:
        print("❌ Coin list update failed.")

# UI Keyboards
def get_main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("💰 BTC Price"), KeyboardButton("💰 ETH Price")],
        [KeyboardButton("📰 Market News"), KeyboardButton("🤖 AI Analyst")]
    ], resize_keyboard=True)

# Channel Join စစ်ဆေးခြင်း
async def is_subscribed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=update.effective_user.id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# --- COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        keyboard = [
            [InlineKeyboardButton("📢 Channel ကို Join ရန်", url=f"https://t.me/{CHANNEL_ID[1:]}")],
            [InlineKeyboardButton("✅ Join ပြီးပါပြီ (စစ်ဆေးမည်)", callback_data="check_join")]
        ]
        await update.message.reply_text(
            f"မင်္ဂလာပါ! Bot ကို အသုံးပြုရန် ကျွန်ုပ်တို့၏ Channel ({CHANNEL_ID}) ကို အရင် Join ပေးပါ။ 🙏",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    await update.message.reply_text("Crypto AI Assistant အဆင်သင့်ပါပဲ! ✨", reply_markup=get_main_keyboard())

# Smart Price Fetcher
async def fetch_price(update: Update, coin_symbol: str):
    coin_symbol = coin_symbol.lower().strip()
    coin_id = COIN_MAP.get(coin_symbol, coin_symbol)
    
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
    try:
        res = requests.get(url).json()
        if coin_id in res:
            p = res[coin_id]['usd']
            c = res[coin_id]['usd_24h_change']
            trend = "📈" if c > 0 else "📉"
            await update.message.reply_text(f"💰 **{coin_id.upper()}**\nPrice: ${p:,}\n24h: {trend} {c:.2f}%")
        else:
            await update.message.reply_text("❌ Coin ရှာမတွေ့ပါ။ ဥပမာ- /price bnb")
    except:
        await update.message.reply_text("ဈေးနှုန်းရယူရာတွင် အခက်အခဲရှိနေပါသည်။")

# AI Logic
async def ai_query(update: Update, text: str):
    status_msg = await update.message.reply_text("AI စဉ်းစားနေပါသည်... 🧠")
    try:
        response = await asyncio.to_thread(model.generate_content, f"Answer in Burmese: {text}")
        await status_msg.edit_text(response.text)
    except Exception as e:
        await status_msg.edit_text(f"Error: {str(e)}")

# News Logic
async def get_market_news(update: Update):
    status_msg = await update.message.reply_text("သတင်းများ စုစည်းနေပါသည်... ⏳")
    try:
        data = requests.get("https://cryptopanic.com/api/v1/posts/?auth_token=PUBLIC&public=true").json()
        titles = [n['title'] for n in data['results'][:5]]
        summary_prompt = f"Summarize these crypto news in Burmese: {' | '.join(titles)}"
        response = await asyncio.to_thread(model.generate_content, summary_prompt)
        await status_msg.edit_text(f"📰 **Latest News Summary:**\n\n{response.text}")
    except:
        await status_msg.edit_text("သတင်းဆွဲယူလို့ မရနိုင်သေးပါ။")

# --- MESSAGE HANDLERS ---
async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Private Chat မှာ Join မ Join အရင်စစ်မယ်
    if update.effective_chat.type == "private" and not await is_subscribed(update, context):
        await start(update, context)
        return

    text = update.message.text
    if not text: return

    # Buttons Handling
    if text == "💰 BTC Price": await fetch_price(update, "bitcoin")
    elif text == "💰 ETH Price": await fetch_price(update, "ethereum")
    elif text == "📰 Market News": await get_market_news(update)
    elif text == "🤖 AI Analyst": await update.message.reply_text("သိချင်တာကို /ai [မေးခွန်း] သို့မဟုတ် /price [coin] လို့ ရိုက်ပါ။")
    
    # Mention in Groups
    elif f"@{context.bot.username}" in text:
        query = text.replace(f"@{context.bot.username}", "").strip()
        if query: await ai_query(update, query)

# --- CALLBACK HANDLERS ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "check_join":
        if await is_subscribed(update, context):
            await query.edit_message_text("Join တာ အောင်မြင်ပါတယ်။ 🎉")
            await query.message.reply_text("စတင်အသုံးပြုနိုင်ပါပြီ။", reply_markup=get_main_keyboard())
        else:
            await query.answer("မ Join ရသေးပါဘူးဗျာ။ အရင် Join ပေးပါ။", show_alert=True)

# Main Function
if __name__ == '__main__':
    refresh_coin_list()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ai", lambda u, c: ai_query(u, " ".join(c.args)) if c.args else u.message.reply_text("မေးခွန်းထည့်ပါ။")))
    app.add_handler(CommandHandler("price", lambda u, c: fetch_price(u, c.args[0]) if c.args else u.message.reply_text("Coin အမည်ထည့်ပါ။")))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_all_messages))
    
    print("🚀 Pro Crypto Bot is running...")
    app.run_polling()