import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import random
import json
import os

class App:
    def __init__(self):
        self.base_url = 'https://www.transfermarkt.com'
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com"
            }  
        self.team_file = 'team.json'
        self.player_file = 'player.json'
        self.failed_file = 'failed.json'
        

    def delay(self):
        time.sleep(random.uniform(5, 10))
        
    def get_response(self, url, retries=3):
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=self.headers)
                if response.status_code == 200:
                    return response
                else:
                    print(f"  [!] Attempt {attempt+1}: Status {response.status_code}")
                    time.sleep(20)
            except requests.exceptions.RequestException as e:
                print(f"  [!] Request error: {e}")
                time.sleep(20)
        return None

    def get_teams(self, league, league_code, season):
        if os.path.exists(self.team_file):
            with open(self.team_file, 'r') as f:
                teams = json.load(f)
            print("team list already exist")
            return teams
                
        else:
            print("Getting team list...")
            url = f'{self.base_url}/{league}/startseite/wettbewerb/{league_code}/plus/?saison_id={season}'
            response = self.get_response(url)

            if not response:
                print("Failed to load the page")
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            teams = []
            tbody = soup.find_all("tbody")

            for i in tbody:
                tr = i.find_all("tr", {"class": ["odd", "even"]})
                for j in tr:
                    td = j.find_all("td", {"class": "zentriert no-border-rechts"})
                    for k in td:
                        a = k.find("a")
                        if a and 'href' in a.attrs:
                            teams.append(a["href"].strip())

            with open(self.team_file, 'w') as f:
                json.dump(teams, f)

            return teams

    def get_players(self, league, league_code, season, retry_again=False):
        if retry_again and os.path.exists(self.failed_file):
            with open(self.failed_file, 'r') as f:
                teams = json.load(f)
        else:
            teams = self.get_teams(league, league_code, season)
            
        succeed = []
        
        if os.path.exists(self.failed_file):
            with open(self.failed_file, 'r') as f:
                failed = json.load(f)
        else:
            failed = []
            
        for idx, team in enumerate(teams):
            full_url = self.base_url + team
            print(f"[{idx+1}/{len(teams)}] Team: {full_url}")
            
            response = self.get_response(full_url)
            if not response:
                print(f"  Failed to load the page: {full_url}")  
                if team not in failed:
                    failed.append(team)
                    
                continue
            try:        
                soup = BeautifulSoup(response.text, "html.parser")
                tables = soup.find_all("table", {"class": "inline-table"})

                for table in tables:
                    rows = table.find_all("tr")
                    for row in rows:
                        td = row.find("td", {"class": "hauptlink"})
                        if td:
                            a_tag = td.find("a")
                            if a_tag and 'href' in a_tag.attrs:
                                player_link = a_tag["href"]
                                stats_link = player_link.replace('profil', 'leistungsdaten')
                                full_stats_link = f"{self.base_url}{stats_link}/saison/2024/plus/0?saison=2024"
                                succeed.append(full_stats_link)

                if team in failed:
                    failed.remove(team)
            
            except Exception as e:
                print(f"  [!] Parsing error: {e}")
                if team not in failed:
                    failed.append(team)
                
            self.delay()
            
        with open(self.failed_file, 'w') as f:
            json.dump(failed, f, indent= 2)
        
        if os.path.exists(self.player_file):
            with open(self.player_file, 'r') as f:
                succeeds = json.load(f)
        else:
            succeeds = []
            
        combined = list(set(succeeds + succeed))
        with open(self.player_file, 'w') as f:
            json.dump(combined, f, indent= 2)
            
        
if __name__ == "__main__":
    player_scraper = App()
    
    league = input("Enter league name (e.g. premier-league): ")
    league_code = input("Enter league code (e.g. GB1): ")
    season = input("Enter season year (e.g. 2024): ")

    try:
        season = int(season)
    except ValueError:
        print("Season must be a number (e.g. 2024)")
        exit()
    
    player_scraper.get_players(league, league_code, season)
