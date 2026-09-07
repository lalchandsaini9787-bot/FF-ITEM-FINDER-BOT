import os
import telebot
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8807823919:AAEUXwCYO6hgLrxxfbhisGIYSgB4FG-Gbk4")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, f"Hello {m.from_user.first_name} 👋\nBot is Live! Ab item ka naam bhejo.")

@bot.message_handler(func=lambda m: True)
def search(m):
    if m.text.startswith('/'): return
    bot.send_message(m.chat.id, f"Tumne bheja: {m.text}\nAb mai FF items wala feature add kar dunga.")

@app.route('/')
def home():
    return "Bot Running OK"

@app.route('/webhook', methods=['POST'])
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    try:
        data = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(data)
        bot.process_new_updates([update])
    except Exception as e:
        print(f"Error: {e}")
    return "ok", 200
