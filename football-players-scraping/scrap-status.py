import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import csv
import time
import random
import json
import pandas as pd


class App:
    def __init__(self, players_json, competition_name):
        self.competiiton_name = competition_name
        
        with open(players_json, 'r') as f:
            self.players = json.load(f)
            
        self.headers = {"User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com"}

    def delay(self):
        time.sleep(random.uniform(4, 6))
        
    def get_response(self, url, retries=2):
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=self.headers)
                if response.status_code == 200:
                    return response
                else:
                    print(f"  [!] Attempt {attempt+1}: Status {response.status_code}")
                    time.sleep(12)
            except requests.exceptions.RequestException as e:
                print(f"  [!] Request error: {e}")
                time.sleep(5)
        return None
    
    def get_player_info(self):
        all_keys = set()
        all_data = []
        
        for url in self.players:
            name = url.split('/leistungsdaten')[0].split('com/')[1].replace("-", " ").title().strip()
            print(f"Scraping: {name}")
            response = self.get_response(url)
            
            if not response:
                print("Failed to load the page")
                continue
            try :
                soup = BeautifulSoup(response.text, "html.parser")
                
                info = {}
                info["Name"] = name
                
                data = soup.find_all("li", {"class":"data-header__label"})
                
                for item in data:
                    label = item.get_text(strip=True).split(":")[0]
                    content_tag = item.find("span", {"class":"data-header__content"})
                    
                    if not content_tag:
                        continue
                    content = content_tag.get_text(strip=True)
                    if "Date of birth/Age" in label:
                        info["Date of Birth"] = content.split("(")[0].strip()
                    elif "Citizenship" in label:
                        info["Nationality"] = content
                    elif "Height" in label:
                        info["Height (cm)"] = int(float(content.replace(',', '.').replace('m', '').strip()) * 100)
                    elif "Position" in label:
                        info["Position"] = content    
                
                table = soup.find("table", {"class":"items"})

                titles, status = [], []

                thead = table.find("thead")
                if thead:
                    th = thead.find_all("th")
                    for item in th:
                        span = item.find("span")
                        if span and span.has_attr("title"):
                            titles.append(span["title"])
                # print(titles)

                tbody = table.find("tbody")
                tr = tbody.find_all("tr", {"class":["odd","even"]})
                for tr_row in tr:
                    td_league = tr_row.find("td", {"class":"hauptlink no-border-rechts"})
                    if td_league and td_league.find("img") and td_league.find("img")["title"] == self.competition_name:
                        td =  tr_row.find_all("td", {"class":["zentriert", "rechts"]})
                        for td_row in td:
                            status.append(td_row.get_text(strip=True))
                if status == []:
                    status = ['-'] * len(titles)
                # print(status)   
                    
                final = dict(zip(titles, status))
                info.update(final)
                
                all_keys.update(info.keys())
                all_data.append(info)
                
                self.delay()
            
            except Exception as e:
                print(f"  [!] Parsing error {url}: {e}")
                
        return all_data
    
    def create_excel(self):
        excel_file = "Premier-League-Player-Stats-2024-2025.xlsx"
        cols = [
            "Name", "Date of Birth", "Nationality", 
            "Height (cm)", "Position", "Appearances", 
            "Minutes played" ,"Goals", "Assists", "Clean sheets", 
            "Goals conceded", "Yellow cards", "Second yellow cards", "Red cards"
            ]
        all_data = self.get_player_info()

        clean_data = []
        
        for data in all_data:
            clean_row = {}
            for k in cols:
                v = data.get(k, 0)
                clean_row[k] = 0 if v in ['', '-', None, 'NaN', 'nan'] else v
            clean_data.append(clean_row)
            
        df = pd.DataFrame(clean_data)
        df = df[cols]
        df.to_excel(excel_file, index=False)
            
                
        print(f"Done. Number of players: {len(all_data)}. saved at: {excel_file}")
        
if __name__ == "__main__":
    player_json = input("Enter path to player JSON file (e.g. premier-league-players-2024.json): ")
    competition_name = input("Enter competition name (e.g. Premier League): ")
    
    start_time = time.time()
    print("Starting...")
    
    status_scraper = App(player_json, competition_name)
    status_scraper.create_excel()
    
    end_time = time.time()
    duration = (end_time - start_time) / 60
    print(f"Duration: {round(duration, 2)} minutes")
        

            