import telebot
import os
from dotenv import load_dotenv
from debug.recommendations import recommendations
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

load_dotenv()
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
        bot.send_message(message.chat.id, "Select a country:", reply_markup=markup)
    except Exception as e:
        print(f"Error in start command: {e}")

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
            user_state[call.from_user.id].update({'region': region})
            
            bot.send_message(call.message.chat.id, "Please enter the start date in the format YYYYMMDD (e.g., 20240801):")
            user_state[call.from_user.id]['awaiting_start_date'] = True

        elif data == "cancel":
            start(call.message)

    except Exception as e:
        print(f"Error in callback handling: {e}")

@bot.message_handler(func=lambda message: message.from_user.id in user_state and user_state[message.from_user.id].get('awaiting_start_date'))
def handle_start_date_input(message):
    user_id = message.from_user.id
    start_date_str = message.text

    try:
        start_date = datetime.strptime(start_date_str, '%Y%m%d')
        
        if start_date < datetime.now():
            bot.send_message(message.chat.id, "Error: The start date must be today or a future date. Please enter a valid start date.")
            return
        
        user_state[user_id]['start_date'] = start_date
        user_state[user_id]['start_date_str'] = start_date_str
        bot.send_message(message.chat.id, "Please enter the end date in the format YYYYMMDD (e.g., 20240807):")
        user_state[user_id]['awaiting_start_date'] = False
        user_state[user_id]['awaiting_end_date'] = True

    except ValueError:
        bot.send_message(message.chat.id, "Error: Invalid start date format. Please enter the date in the format YYYYMMDD.")

@bot.message_handler(func=lambda message: message.from_user.id in user_state and user_state[message.from_user.id].get('awaiting_end_date'))
def handle_end_date_input(message):
    user_id = message.from_user.id
    end_date_str = message.text

    try:
        end_date = datetime.strptime(end_date_str, '%Y%m%d')
        start_date = user_state[user_id].get('start_date')

        if end_date <= start_date:
            bot.send_message(message.chat.id, "Error: The end date must be after the start date. Please enter a valid end date.")
            return
        
        user_state[user_id]['end_date'] = end_date
        user_state[user_id]['end_date_str'] = end_date_str

        country = user_state[user_id]['country']
        region = user_state[user_id]['region']
        bars_list = recommendations[country][region]  # Dummy data, replace with actual filtering logic
        
        bumped_bars = [f"<b>{bar['name']}</b> - <i>Bumped to Top</i> ({bar['url']})" for bar in bars_list if bar.get('paid')]
        regular_bars = [f"<b>{bar['name']}</b> ({bar['url']})" for bar in bars_list if not bar.get('paid')]

        bars_text = '\n'.join(bumped_bars + regular_bars)
        urls_text = '\n'.join([bar['url'] for bar in bars_list])

        start_date_str = user_state[user_id].get('start_date_str')
        end_date_str = user_state[user_id].get('end_date_str')

        markup = InlineKeyboardMarkup()
        markup.row_width = 2
        markup.add(
            InlineKeyboardButton("Other regions?", callback_data=f"country:{country}"),
            InlineKeyboardButton("Select Another Country", callback_data="cancel")
        )
        bot.send_message(
            message.chat.id, 
            f"Here are some bar recommendations for {region} in {country} from {start_date_str} to {end_date_str}:\n\n{bars_text}\n\nLinks:\n{urls_text}", 
            reply_markup=markup,
            parse_mode='HTML'
        )

        user_state[user_id].pop('awaiting_end_date', None)
        user_state[user_id].pop('start_date', None)
        user_state[user_id].pop('end_date', None)

    except ValueError:
        bot.send_message(message.chat.id, "Error: Invalid end date format. Please enter the date in the format YYYYMMDD.")

try:
    bot.infinity_polling()
except Exception as e:
    print(f"Error in polling: {e}")