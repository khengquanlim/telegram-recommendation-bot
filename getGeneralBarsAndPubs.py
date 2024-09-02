import googlemaps
import pandas as pd
import os
from dotenv import load_dotenv
import time

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")

gmaps = googlemaps.Client(key=google_api_key)

singapore_locations = {
    "1.3521,103.8198": "Central Singapore",
    "1.290270,103.851959": "Downtown",
    "1.440350,103.830320": "North",
    "1.280095,103.849881": "South",
    "1.352083,103.819836": "East",
    "1.352083,103.706836": "West",
}

def get_bars_and_pubs(location, location_name, radius=1000):
    try:
        places_result = gmaps.places_nearby(
            location=location,
            radius=radius,
            type='bar'
        )
    except googlemaps.exceptions.ApiError as e:
        print(f"API Error for location {location}: {e}")
        return []

    def convert_price_level(price_level):
        price_mapping = {
            0: '$',
            1: '$',
            2: '$$',
            3: '$$$',
            4: '$$$$'
        }
        return price_mapping.get(price_level, 'Not available')
    
    bar_data = []
    for place in places_result.get('results', []):
        name = place.get('name')
        address = place.get('vicinity')
        price_level_raw = place.get('price_level', 'Not available')
        price_level = convert_price_level(price_level_raw)

        # opening_hours = 'Not available'
        # place_id = place.get('place_id')
        # if place_id:
        #     try:
        #         details = gmaps.place(place_id=place_id, fields=['opening_hours'])
        #         opening_hours = details.get('result', {}).get('opening_hours', {}).get('weekday_text', 'Not available')
        #     except googlemaps.exceptions.ApiError as e:
        #         print(f"Error fetching details for place_id {place_id}: {e}")
        
        bar_data.append({
            'Name': name,
            'Address': address,
            'Price Level': price_level,
            'Location': location_name
            # 'Opening Hours': opening_hours
        })
    
    return bar_data

def fetch_and_save_bars_data(filename='bars_and_pubs_singapore.csv'):
    all_bars_data = []
    for location, location_name in singapore_locations.items():
        print(f"Fetching bars and pubs for location: {location}")
        bars_and_pubs = get_bars_and_pubs(location, location_name, radius=1000)
        all_bars_data.extend(bars_and_pubs)
        time.sleep(2)
    
    df = pd.DataFrame(all_bars_data)
    df.drop_duplicates(subset=['Name', 'Address'], inplace=True) 
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")