# Telegram Bot for Bar Recommendations

This Telegram bot provides information on available bars in Singapore. It retrieves data from the Google Places API, saves it to Google Drive, and then uses this data to make recommendations.

## Features

1. **Data Retrieval**: 
   - Retrieves bar data from the Google Places API based on region locations in Singapore.
   - Saves the retrieved data to a local Google Drive folder.

2. **Data Processing**: 
   - Retrieves CSV files from the local Google Drive (requires manual data cleaning or updates).
   - Saves the cleaned CSV to your local computer for use.

## Setup

### Dependencies

To install the required dependencies, use the following command:

```pip install -r requirements.txt```

To Run the bot:
1. Run the main script:

```python main.py```

2.Run the recommendation bot script:

```python recommendBot.py```

## Future Improvements
Clean up and refactor the code for better maintainability.
Enhance data processing and integration features.
