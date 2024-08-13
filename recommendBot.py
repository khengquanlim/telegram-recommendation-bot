import telebot
import os
from dotenv import load_dotenv
from debug.recommendations import recommendations
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Load the .env file
load_dotenv()

# Get the token from environment variables
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(bot_token)

user_state = {}

@bot.message_handler(commands=['start'])
def start(message):
    try:
        markup = InlineKeyboardMarkup()
        markup.row_width = 2
        markup.add(
            InlineKeyboardButton("Singapore", callback_data="country:Singapore"),
            InlineKeyboardButton("Malaysia", callback_data="country:Malaysia"),
            InlineKeyboardButton("Vietnam", callback_data="country:Vietnam"),
            InlineKeyboardButton("Thailand", callback_data="country:Thailand")
        )
    except Exception as e:
        print(f"Error in start command: {e}")

    bot.send_message(message.chat.id, "Select a country:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        data = call.data

        user_id = call.from_user.id

        if user_id not in user_state:
            user_state[user_id] = {}

        if data.startswith("country:"):
            country = data.split(":")[1]
            user_state[call.from_user.id] = {'country': country}

            markup = InlineKeyboardMarkup()
            markup.row_width = 2
            regions = ['North', 'South', 'East', 'West']
            buttons = [InlineKeyboardButton(region, callback_data=f"region:{region}:{country}") for region in regions]
            markup.add(*buttons)
            markup.add(InlineKeyboardButton("Cancel", callback_data="cancel"))

            bot.send_message(call.message.chat.id, f"Select a region in {country}:", reply_markup=markup)

        elif data.startswith("region:"):
            region, country = data.split(":")[1], data.split(":")[2]

            try:
                bars_list = recommendations[country][region]
                bumped_bars = [f"<b>{bar['name']}</b> - <i>Bumped to Top</i> ({bar['url']})" for bar in bars_list if bar['paid']]
                regular_bars = [f"<b>{bar['name']}</b> ({bar['url']})" for bar in bars_list if not bar['paid']]
                
                bars_text = '\n'.join(bumped_bars + regular_bars)
                
                urls_text = '\n'.join([bar['url'] for bar in bars_list])

                markup = InlineKeyboardMarkup()
                markup.row_width = 2
                markup.add(
                    InlineKeyboardButton("Other regions?", callback_data=f"country:{country}"),
                    InlineKeyboardButton("Select Another Country", callback_data="cancel")
                )
                bot.send_message(
                    call.message.chat.id, 
                    f"Here are some bar recommendations for {region} in {country}:\n\n{bars_text}\n\nLinks:\n{urls_text}", 
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            except KeyError as e:
                bot.send_message(call.message.chat.id, "Sorry, there was an error fetching recommendations. Please try again.")
                print(f"Error: {e}")

        elif data == "cancel":
            start(call.message)
    
    except Exception as e:
        print(f"Error in callback handling: {e}")
        
try:
    bot.infinity_polling()
except Exception as e:
    print(f"Error in polling: {e}")