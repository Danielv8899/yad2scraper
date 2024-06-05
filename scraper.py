import requests
import json
import os.path
import argparse
import time

TLV_CODE = 5000

def get_city(city_str):
    match city_str:
        case "tlv":
            return TLV_CODE

def hashfunc(entry):

    token = str(entry["token"])
    price = str(entry["price"])

    return hash(token+price)

class yad2Scraper:

    def __init__(self,rooms_min,rooms_max,min_price,max_price,city_code,filter_commercial) -> None:
        self.domain: str = "yad2.co.il"
        self.rooms_min: str = rooms_min
        self.rooms_max: str = rooms_max
        self.min_price: str = min_price
        self.max_price: str = max_price
        self.city_code:int = city_code
        self.listings_path: str = "listings.json"
        self.listings_url: str = f"https://gw.{self.domain}:443/realestate-feed/rent/map?minPrice={self.min_price}&maxPrice={self.max_price}&minRooms={self.rooms_min}&maxRooms={self.rooms_max}&city={self.city_code}"
        self.entry_url_base: str = f"https://www.yad2.co.il:443/realestate/item/"
        self.filter_commercial: bool = filter_commercial
        self.listings = {}

        self.init_listings()

    def init_listings(self):
        res = self.load_listings()
        if not res:
            self.listings = self.pull_listings()
            self.flush_listings()
    
    def flush_listings(self):
        with open(self.listings_path,"w") as f:
            json.dump(self.listings,f)
    
    def load_listings(self):
        if not os.path.exists(self.listings_path):
            return False
        
        with open(self.listings_path) as f:
            data = json.load(f)

            self.listings = data
            return True


    def pull_listings(self):
        r = requests.get(self.listings_url)
        data = r.json()["data"]["markers"]

        assert data is not None or {}

        if self.filter_commercial:
            filtered_data = []
            for i in range(len(data)):
                    if data[i]["adType"] == "private":
                        filtered_data.append(data[i])
            
            data = filtered_data

        return data

    def check_new_listings(self):
        new_listing: dict = self.pull_listings()

        assert new_listing is not None or {}

        entry_hashes = [hashfunc(x) for x in self.listings]

        new_entries = []

        for entry in new_listing:
            if hashfunc(entry) not in entry_hashes:
                new_entries.append(entry)
                self.listings.append(entry)
        
        self.flush_listings()

        return new_entries
    
    def get_links(self,entries):
        return [{self.entry_url_base + x["token"],x["price"]} for x in entries]
    
    def loop(self):
        while True:
            new_entries = self.check_new_listings()
            print(self.get_links(new_entries))
            time.sleep(60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("rooms_min")
    parser.add_argument("rooms_max")
    parser.add_argument("price_min")
    parser.add_argument("price_max")
    parser.add_argument("city")
    parser.add_argument("-f","--filter-commercial",action="store_true",help="filter commercial entries",default=False)

    args = parser.parse_args()

    scraper = yad2Scraper(args.rooms_min,args.rooms_max,args.price_min,args.price_max,get_city(args.city),args.filter_commercial)
    scraper.loop()


# burp0_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.112 Safari/537.36", "Accept": "*/*", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-User": "?1", "Sec-Fetch-Dest": "document", "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "en-US,en;q=0.9", "Priority": "u=0, i", "Connection": "keep-alive"}
