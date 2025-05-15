import mysql.connector
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from bs4 import BeautifulSoup
import time
import re

load_dotenv()

MYSQL_HOST="localhost"
MYSQL_USER="root"
MYSQL_PASS="test"
MYSQL_DB="olx_scrape"

romanian_months = {
    "ianuarie": "01",
    "februarie": "02",
    "martie": "03",
    "aprilie": "04",
    "mai": "05",
    "iunie": "06",
    "iulie": "07",
    "august": "08",
    "septembrie": "09",
    "octombrie": "10",
    "noiembrie": "11",
    "decembrie": "12"
}

def hm_from_timedelta(td):
    total = int(td.total_seconds())
    h = total // 3600
    m = (total % 3600) // 60
    return f"{h:02d}:{m:02d}"
    
def extract_price(price_str):
    # Extract the numeric part of the price string
    match = re.search(r'\d+', price_str.replace('.', '').replace(',', ''))
    return int(match.group()) if match else 0

def parse_date(scraped_date: str):
    scraped_date = scraped_date.lower().strip()

    # Reactualizat Azi la 12:32
    if "reactualizat azi la" in scraped_date:
        time_part = scraped_date.split("la")[1].strip()
        date_part = datetime.now().date()
        reactualizat = 1

    # Azi la 10:21
    elif "azi la" in scraped_date:
        time_part = scraped_date.split("la")[1].strip()
        date_part = datetime.now().date()
        reactualizat = 0

    # Reactualizat la 20 aprilie 2025
    elif "reactualizat la" in scraped_date:
        date_str = scraped_date.replace("reactualizat la", "").strip()
        day, month_name, year = date_str.split()
        month = romanian_months[month_name]
        date_part = datetime.strptime(f"{day}-{month}-{year}", "%d-%m-%Y").date()
        time_part = "00:00"
        reactualizat = 1

    # 14 aprilie 2025
    else:
        day, month_name, year = scraped_date.split()
        month = romanian_months[month_name]
        date_part = datetime.strptime(f"{day}-{month}-{year}", "%d-%m-%Y").date()
        time_part = "00:00"
        reactualizat = 0

    return date_part, time_part, reactualizat


def searchRents(city, type, url):
    

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    cnx = mysql.connector.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASS, database=MYSQL_DB)
    cursor = cnx.cursor(dictionary=True)

    insert_query = f'INSERT INTO listings (type, title, date, time, location, price, link, reactualizat, sent) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
    check_query = f'SELECT title, price, date, time FROM listings WHERE link = %s'
    update_query = f'UPDATE listings SET type = %s, title= %s, date = %s, time = %s, location = %s, price = %s, reactualizat = %s, sent = 0 WHERE link = %s'

    listings = soup.find_all(class_='css-qfzx1y')
    
    #links = ["https://olx.ro" + a['href'] for a in soup.find_all('a', {'class': 'css-1tqlkj0'})]

    forbidden_keywords = ["manastur", "bulgaria", "dambul", "grigorescu", "muresanu", "zorilor", "gruia", "iris"]

    count_skipped = 0
    for listing in listings:
        link = ""
        try:
            link_tag = listing.find('a', class_='css-1tqlkj0')
            link = "https://olx.ro" + link_tag['href'] if link_tag else None
            if not link:
                raise RuntimeError("No link found in this listing container")

            # Proceed to extract title, date, etc. from this `listing`
        except Exception as e:
            print(f"❌ Failed to parse a listing: {e}")
            continue

        scrapedTitle = listing.find(class_='css-1g61gc2').text
        scrapedDate = listing.find(class_='css-vbz67q').text
        scrapedPrice = listing.find(class_='css-uj7mm0').text

        title = scrapedTitle.lower()
        location = scrapedDate.split(" - ")[0]
        price = scrapedPrice.split("€")[0]+" euro"
        date = scrapedDate.split(" - ")[1]
        
        if "storia.ro" in link:
            link=link.split("https://olx.ro")[1]

        if any(keyword in title for keyword in forbidden_keywords):
            count_skipped+=1
            continue

        date_added, time, reactualizat = parse_date(date)

        cursor.execute(check_query, (link,))
        result = cursor.fetchall()

        if len(result) != 0:
            db_price = result[0]['price']
            db_date = result[0]['date']
            db_time = result[0]['time']
            
            db_price_value = extract_price(db_price)
            price_value = extract_price(price)

            if abs(db_price_value - price_value) >= 5:
                print(f"💸 Price changed: {title} | {db_price} → {price}")
                cursor.execute(update_query, (type, title, date_added, time, location, price, reactualizat, link))

            db_time_hm = hm_from_timedelta(db_time)
            if reactualizat and (db_date != date_added or db_time_hm != time):
                print(f"📆 Date/time changed: {title} | {db_date} {db_time_hm} → {date_added} {time}")
                cursor.execute(update_query, (type, title, date_added, time, location, price, reactualizat, link))

        else:
            if reactualizat:
                print(f"♻️ Reactualizat: {title} | {price} | {date}")
            else:
                print(f"🆕 Found: {title} | {price} | {date}")

            cursor.execute(insert_query, (type, title, date_added, time, location, price, link, reactualizat, 0))


        cnx.commit()
        #print("\nFinish APARTMENT: \n\n")
    print(f'[OLX • {datetime.now().strftime("%H:%M")}] Searching in {city.capitalize()} for {type.capitalize()}. -> Found {len(listings)-count_skipped}/{len(listings)} listings')

    cursor.close()
    cnx.close()


starttime = time.time()
while True:
    CITY="cluj-napoca"
    TYPE="2camere"
    URL="https://www.olx.ro/imobiliare/apartamente-garsoniere-de-inchiriat/2-camere/cluj-napoca/?currency=EUR&search%5Border%5D=created_at:desc&search%5Bfilter_float_price:from%5D=200&search%5Bfilter_float_price:to%5D=500"
    searchRents(CITY, TYPE, URL)

    CITY="cluj-napoca"
    TYPE="garsoniera"
    URL="https://www.olx.ro/imobiliare/apartamente-garsoniere-de-inchiriat/1-camera/cluj-napoca/?currency=EUR&search%5Bfilter_float_price%3Afrom%5D=200&search%5Bfilter_float_price%3Ato%5D=500&search%5Border%5D=created_at%3Adesc"
    searchRents(CITY, TYPE, URL)
    
    time.sleep(60.0 - ((time.time() - starttime) % 60.0))