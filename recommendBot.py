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

def send_country_selection(message):
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("Singapore", callback_data="country:Singapore"),
        InlineKeyboardButton("Malaysia", callback_data="country:Malaysia"),
        InlineKeyboardButton("Vietnam", callback_data="country:Vietnam"),
        InlineKeyboardButton("Thailand", callback_data="country:Thailand")
    ]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "Select a country:", reply_markup=markup)

def send_region_selection(message, country):
    markup = InlineKeyboardMarkup(row_width=2)
    regions = ['North', 'South', 'East', 'West']
    buttons = [InlineKeyboardButton(region, callback_data=f"region:{region}:{country}") for region in regions]
    markup.add(*buttons)
    markup.add(InlineKeyboardButton("Cancel", callback_data="cancel"))
    bot.send_message(message.chat.id, f"Select a region in {country}:", reply_markup=markup)

def validate_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y%m%d')
    except ValueError:
        return None

@bot.message_handler(commands=['start'])
def start(message):
    try:
        send_country_selection(message)
    except Exception as e:
        print(f"Error in start command: {e}")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        data = call.data
        user_id = call.from_user.id

        if data.startswith("country:"):
            country = data.split(":")[1]
            user_state[user_id] = {'country': country}
            send_region_selection(call.message, country)

        elif data.startswith("region:"):
            region, country = data.split(":")[1], data.split(":")[2]
            user_state[user_id] = {'country': country, 'region': region, 'awaiting_start_date': True}
            bot.send_message(call.message.chat.id, "Please enter the start date in the format YYYYMMDD (e.g., 20240801):")

        elif data == "cancel":
            start(call.message)

    except Exception as e:
        print(f"Error in callback handling: {e}")

@bot.message_handler(func=lambda message: message.from_user.id in user_state and user_state[message.from_user.id].get('awaiting_start_date'))
def handle_start_date_input(message):
    user_id = message.from_user.id
    start_date = validate_date(message.text)
    print(start_date)
    print(message.text)
    
    if start_date and start_date >= datetime.now():
        user_state[user_id]['start_date'] = start_date
        user_state[user_id]['start_date_str'] = datetime.strptime(message.text, '%Y%m%d').strftime('%Y-%m-%d')
        print(user_state[user_id]['start_date_str'])
        bot.send_message(message.chat.id, "Please enter the end date in the format YYYYMMDD (e.g., 20240807):")
        user_state[user_id]['awaiting_start_date'] = False
        user_state[user_id]['awaiting_end_date'] = True
    else:
        bot.send_message(message.chat.id, "Error: Invalid start date format or past date. Please enter a valid start date.")

@bot.message_handler(func=lambda message: message.from_user.id in user_state and user_state[message.from_user.id].get('awaiting_end_date'))
def handle_end_date_input(message):
    user_id = message.from_user.id
    end_date = validate_date(message.text)
    start_date = user_state[user_id].get('start_date')

    if end_date and end_date > start_date:
        user_state[user_id]['end_date'] = end_date
        country = user_state[user_id]['country']
        region = user_state[user_id]['region']
        bars_list = recommendations.get(country, {}).get(region, [])

        bumped_bars = [f"<b>{bar['name']}</b> - <i>Bumped to Top</i> ({bar['url']})" for bar in bars_list if bar.get('paid')]
        regular_bars = [f"<b>{bar['name']}</b> ({bar['url']})" for bar in bars_list if not bar.get('paid')]

        bars_text = '\n'.join(bumped_bars + regular_bars)
        urls_text = '\n'.join([bar['url'] for bar in bars_list])

        user_state[user_id]['end_date_str'] = datetime.strptime(message.text, '%Y%m%d').strftime('%Y-%m-%d')
        start_date_str = user_state[user_id].get('start_date_str')
        end_date_str = user_state[user_id].get('end_date_str')

        markup = InlineKeyboardMarkup(row_width=2)
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

        user_state[user_id].clear()  # Clear the user state after processing

    else:
        bot.send_message(message.chat.id, "Error: Invalid end date format or date is not after start date. Please enter a valid end date.")

try:
    bot.infinity_polling()
except Exception as e:
    print(f"Error in polling: {e}")

# def send_start_date_calendar(message):
#     calendar, step = DetailedTelegramCalendar().build()
#     bot.send_message(message.chat.id,
#                      f"Select {LSTEP[step]}",
#                      reply_markup=calendar)
#     print("Test 4")

# def send_end_date_calendar(message):
#     calendar, step = DetailedTelegramCalendar().build()
#     markup = InlineKeyboardMarkup()
#     bot.send_message(message.chat.id, "Please select the end date:", reply_markup=markup)


# @bot.callback_query_handler(func=DetailedTelegramCalendar.func())
# def cal(c):
#     result, key, step = DetailedTelegramCalendar().process(c.data)
#     if not result and key:
#         bot.edit_message_text(f"Select {LSTEP[step]}",
#                               c.message.chat.id,
#                               c.message.message_id,
#                               reply_markup=key)
#     elif result:
#         bot.edit_message_text(f"You selected {result}",
#                               c.message.chat.id,
#                               c.message.message_id)
                              