from getGeneralBarsAndPubs import fetch_and_save_bars_data
from uploadBarsAndPubsToGoogleDrive import upload_to_google

def main():
    fetch_and_save_bars_data('bars_and_pubs_singapore.csv')
    
    upload_to_google('bars_and_pubs_singapore.csv')

if __name__ == '__main__':
    main()