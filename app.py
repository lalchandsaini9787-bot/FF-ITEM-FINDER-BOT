import os
import difflib
import requests
import telebot
from telebot import types
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8807823919:AAEUXwCYO6hgLrxxfbhisGIYSgB4FG-Gbk4")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

ALL_ITEMS = []
try:
    r = requests.get("https://ffitems.vercel.app/api/data/items", timeout=20)
    ALL_ITEMS = r.json()
except:
    pass

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

def aesthetic_card(item):
    name = item.get('name','Unknown')
    item_id = item.get('itemID','')
    icon = item.get('iconName','')
    typ = item.get('type','')
    rare = item.get('rarity','')
    desc = item.get('description','')
    return f"╭─ {name} ─╮\n🆔 ID: {item_id}\n🐼 Icon: {icon}\n📌 Type: {typ} | ✨ {rare}\n📝 {desc}\n╰─ https://ffitems.vercel.app/?q={item_id} ─╯"

@bot.message_handler(commands=['start'])
def start(m):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔍 Search Item", callback_data="search"))
    bot.send_message(m.chat.id, f"Hello {m.from_user.first_name} 👋\nWelcome to FF Items Vault.\nName / ID bhejo, image ke saath ayega.", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    msg = bot.send_message(c.message.chat.id, "Item name / ID bhejo:")
    bot.register_next_step_handler(msg, process_search)

def process_search(m):
    q = m.text.strip()
    if not q or q.startswith('/'):
        return
    wait = bot.send_message(m.chat.id, f"Searching for {q}...")
    results = find_items(q)
    try:
        bot.delete_message(m.chat.id, wait.message_id)
    except:
        pass
    if not results:
        bot.send_message(m.chat.id, f"Nothing found for {q}")
        return
    for item in results[:3]:
        caption = aesthetic_card(item)
        icon = item.get('iconName','')
        img_url = f"https://raw.githubusercontent.com/fakestarexx/FFItems/master/assets/items/{icon}.png"
        try:
            bot.send_photo(m.chat.id, img_url, caption=caption)
        except:
            try:
                bot.send_message(m.chat.id, caption)
            except:
                pass
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
@app.route('/webhook', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "ok", 200
