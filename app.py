from flask import Flask, request
import requests, os, time, difflib
import telebot
from telebot import types

app = Flask(__name__)

BOT_TOKEN = "8807823919:AAEUXwCYO6hgLrxxfbhisGIYSgB4FG-Gbk4"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

ALL_ITEMS = []
try:
    r = requests.get("https://ffitems.vercel.app/api/data/items", timeout=20)
    ALL_ITEMS = r.json()
    print(f"Loaded {len(ALL_ITEMS)} items")
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
    welcome = f"Hello, *{m.from_user.first_name}* 👋\n\nWelcome to *FF Items Vault*.\nSend any Name / ID / Code. Even misspelled works.\n\n*What would you like to search?*"
    bot.send_message(m.chat.id, welcome, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    msg = bot.send_message(c.message.chat.id, "Send me the *item name / ID / code*")
    bot.register_next_step_handler(msg, process_search)

def process_search(m):
    q = m.text.strip()
    load = bot.send_message(m.chat.id, "✨ *Searching...*")
    time.sleep(0.6)
    bot.edit_message_text("🔮 *Scanning database...*", m.chat.id, load.message_id)
    time.sleep(0.6)
    bot.edit_message_text(f"⚡️ *Finding for* `{q}`...", m.chat.id, load.message_id)
    results = find_items(q)
    bot.delete_message(m.chat.id, load.message_id)
    if not results:
        bot.send_message(m.chat.id, f"Nothing found for *{q}*")
        return
    for item in results[:5]:
        bot.send_message(m.chat.id, aesthetic_card(item), disable_web_page_preview=True)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔍 Search Again", callback_data="search"))
    bot.send_message(m.chat.id, "Search again?", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def any_text(m):
    process_search(m)

@app.route('/')
def home():
    return "Bot Running"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok"

if __name__ == '__main__':
    bot.remove_webhook()
    bot.infinity_polling()
