import os
import time
import difflib
import requests
import telebot
from telebot import types
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    BOT_TOKEN = "8807823919:AAEUXwCYO6hgLrxxfbhisGIYSgB4FG-Gbk4"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

ALL_ITEMS = []
try:
    r = requests.get("https://ffitems.vercel.app/api/data/items", timeout=20)
    ALL_ITEMS = r.json()
    print(f"Loaded {len(ALL_ITEMS)} items")
except Exception as e:
    print(f"Load failed: {e}")

def find_items(query):
    query = query.lower().strip()
    for item in ALL_ITEMS:
        if query == str(item.get('itemID')).lower() or query == str(item.get('iconName')).lower():
            return [item]
    try:
        r = requests.get(f"https://ffitems.vercel.app/api/items?raw={query}", timeout=10)
        data = r.json()
        if data.get('count',0) > 0:
            return data['results'][:5]
    except:
        pass
    names = [str(i.get('name','')).lower() for i in ALL_ITEMS]
    close = difflib.get_close_matches(query, names, n=5, cutoff=0.5)
    matched = []
    for cn in close:
        for item in ALL_ITEMS:
            if str(item.get('name','')).lower() == cn:
                matched.append(item)
                break
    return matched[:5]

def get_image_url(item):
    # 3-4 possible CDN try karenge
    icon = item.get('iconName','')
    item_id = item.get('itemID','')
    # ye sabse common pattern hai FF items ka
    urls = [
        f"https://free-fire-items.s3.amazonaws.com/{icon}.png",
        f"https://ffitems.vercel.app/api/image/{item_id}",
        f"https://starexx.vercel.app/images/{icon}.png",
        f"https://raw.githubusercontent.com/fakestarexx/FFItems/master/assets/items/{icon}.png"
    ]
    return urls[0] # pehla try karo, fail hua to text bhej dega

def aesthetic_card(item):
    return (
        f"╭─ *{item.get('name')}* ─╮\n"
        f"│ 🆔 ID: `{item.get('itemID')}`\n"
        f"│ 🐼 Icon: `{item.get('iconName')}`\n"
        f"│ 📌 Type: {item.get('type')} | ✨ {item.get('rarity')}\n"
        f"│ 📝 _{item.get('description')}_\n"
        f"╰─ [View](https://ffitems.vercel.app/?q={item.get('itemID')}) ─╯"
    )

@bot.message_handler(commands=['start'])
def start(m):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔍 Search Item", callback_data="search"))
    welcome = f"Hello, *{m.from_user.first_name}* 👋\n\nWelcome to *FF Items Vault*.\nSend any Name / ID / Code. Image ke saath ayega.\n\n*What would you like to search?*"
    bot.send_message(m.chat.id, welcome, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    msg = bot.send_message(c.message.chat.id, "Send me the *item name / ID / code*")
    bot.register_next_step_handler(msg, process_search)

def process_search(m):
    q = m.text.strip()
    if q.startswith('/'): return
    load = bot.send_message(m.chat.id, "✨ *Searching...*")
    time.sleep(0.5)
    bot.edit_message_text(f"⚡️ *Finding for* `{q}`...", m.chat.id, load.message_id)
    results = find_items(q)
    bot.delete_message(m.chat.id, load.message_id)
    if not results:
        bot.send_message(m.chat.id, f"Nothing found for *{q}*")
        return
    for item in results[:5]:
        caption = aesthetic_card(item)
        img_url = get_image_url(item)
        try:
            bot.send_photo(m.chat.id, img_url, caption=caption, parse_mode="Markdown")
        except:
            # agar image fail to text bhejo
            bot.send_message(m.chat.id, caption, disable_web_page_preview=True)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔍 Search Again", callback_data="search"))
    bot.send_message(m.chat.id, "Search again?", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def any_text(m):
    process_search(m)

@app.route('/')
def home():
    return "Bot Running!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "ok", 200
    else:
        return "ok", 200
