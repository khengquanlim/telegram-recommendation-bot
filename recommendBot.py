import os
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

load_dotenv()

google_api_key = os.getenv("GOOGLE_API_KEY")

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(bot_token)

service_account_file = os.getenv("SERVICE_ACCOUNT_FILE")
scopes_from_local = [os.getenv("SCOPES")]
creds = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes_from_local)
drive_service = build('drive', 'v3', credentials=creds)

def download_csv_from_google_drive(file_id, output_file):
    try:
        request = drive_service.files().get_media(fileId=file_id)
        with open(output_file, 'wb') as fh:
            fh.write(request.execute())
        print(f"File downloaded as {output_file}")
    except HttpError as error:
        print(f"An error occurred: {error}")

file_id = os.getenv("FILE_ID")
output_csv = os.getenv("OUTPUT_CSV")

download_csv_from_google_drive(file_id, output_csv)

df = pd.read_csv(output_csv)

def get_bars_by_region(region):
    region_bars = df[df['Location'].str.contains(region, case=False, na=False)]
    return region_bars.to_dict('records')

user_state = {}

def send_region_selection(message):
    markup = InlineKeyboardMarkup(row_width=2)
    regions = ['North', 'South', 'East', 'West', 'Central', 'Downtown']
    buttons = [InlineKeyboardButton(region, callback_data=f"region:{region}") for region in regions]
    markup.add(*buttons)
    markup.add(InlineKeyboardButton("Cancel", callback_data="cancel"))
    bot.send_message(message.chat.id, "Select a region:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    send_region_selection(message)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    data = call.data
    user_id = call.from_user.id

    if data.startswith("region:"):
        region = data.split(":")[1]
        user_state[user_id] = {'region': region}
        bars_list = get_bars_by_region(region)

        bumped_bars = [
            f"{i+1}. <b>{bar['Name']}</b> - <i>Bumped to Top</i>\n Address: {bar['Address']}" +
            (f"\n Price Point: {bar['Price Level']}" if bar['Price Level'] != 'Not available' else "") 
            for i, bar in enumerate(bars_list) if bar.get('paid')
        ]

        regular_bars = [
            f"{i+1+len(bumped_bars)}. <b>{bar['Name']}</b>\n Address: {bar['Address']}" +
            (f"\n Price Point: {bar['Price Level']}" if bar['Price Level'] != 'Not available' else "")
            for i, bar in enumerate(bars_list) if not bar.get('paid')
        ]

        if not bumped_bars and not regular_bars:
            bars_text = "There's currently none available for this area, look at other regions!"
        else:
            bars_text = '\n\n'.join(bumped_bars + regular_bars)
        # urls_text = '\n'.join([bar['Address'] for bar in bars_list])

        today = datetime.now()
        four_weeks_later = today + timedelta(weeks=4)
        today_str = today.strftime('%Y-%m-%d')
        four_weeks_later_str = four_weeks_later.strftime('%Y-%m-%d')

        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("Select Another Region", callback_data="cancel")
        )
        bot.send_message(
            call.message.chat.id, 
            # f"Here are some bar recommendations in Singapore for {region} side from {today_str} to {four_weeks_later_str}:\n\n{bars_text}\n\nLinks:\n{urls_text}", 
            f"Here are some bar recommendations in Singapore for {region} side from {today_str} to {four_weeks_later_str}:\n\n{bars_text}", 
            reply_markup=markup,
            parse_mode='HTML'
        )

        user_state[user_id].clear()

    elif data == "cancel":
        start(call.message)

bot.infinity_polling()
