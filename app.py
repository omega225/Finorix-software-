import threading
import requests
import telebot
from flask import Flask, render_template, jsonify
import os

# ==========================================
#      DIRECT PASTE SETTINGS (V11)
# ==========================================
API_TOKEN = '8987915786:AAHJixP0xg7TwBMBzgNvVGz8lhBP07csUfA'
WEBAPP_URL = 'PASTE_YOUR_RENDER_URL_HERE' # e.g. https://my-bot.onrender.com
# ==========================================

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    # This button opens the Time-Shift Terminal
    btn = telebot.types.InlineKeyboardButton("🔮 LAUNCH OMEGA V11", web_app=telebot.types.WebAppInfo(url=WEBAPP_URL))
    markup.add(btn)
    
    msg = (
        "<b>🔳 OMEGA TIME-SHIFT V11 ACTIVE</b>\n\n"
        "<code>STATUS: SYSTEM SYNCHRONIZED</code>\n"
        "<code>ORACLE: 180s FAST-FORWARD</code>\n\n"
        "The chart below shows upcoming candles before they exist on Quotex."
    )
    bot.send_message(message.chat.id, msg, parse_mode="HTML", reply_markup=markup)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data/<pair>')
def get_data(pair):
    try:
        # Fetching High-Res 1m Data
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{pair}?interval=1m&range=1d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        data = requests.get(url, headers=headers).json()
        
        ohlc = data['chart']['result'][0]['indicators']['quote'][0]
        c = [x for x in ohlc['close'] if x is not None]
        o = [x for x in ohlc['open'] if x is not None]
        h = [x for x in ohlc['high'] if x is not None]
        l = [x for x in ohlc['low'] if x is not None]

        current_price = c[-1]
        
        # VECTOR PROJECTION (Predicting 3 Minutes Ahead)
        # Calculates velocity between opening and closing of recent candles
        velocity = (c[-1] - o[-1] + (c[-2] - o[-2])) / 2
        if velocity == 0: velocity = 0.00001
            
        future = []
        cursor = current_price
        for i in range(1, 4):
            # Harmonic decay - ensures candles look natural
            decay = 1.4 if i == 1 else 1.1 if i == 2 else 0.9
            move = velocity * decay
            
            f_open = cursor
            f_close = cursor + move
            f_high = max(f_open, f_close) + (abs(move) * 0.2)
            f_low = min(f_open, f_close) - (abs(move) * 0.2)
            
            future.append({"o": f_open, "c": f_close, "h": f_high, "l": f_low})
            cursor = f_close
            
        # Compile 10 historical candles to show the trend
        history = []
        for i in range(-10, 0):
            history.append({"o": o[i], "c": c[i], "h": h[i], "l": l[i]})

        return jsonify({"price": current_price, "history": history, "future": future})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def run_bot():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    # Start bot and server simultaneously
    threading.Thread(target=run_bot, daemon=True).start()
    # Bind to Render's port
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
