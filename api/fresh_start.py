import requests
import sqlite3
import os 
import unicodedata
from dotenv import load_dotenv

# Incarcam cheia API
load_dotenv()
API_KEY = os.getenv("API_KEY")
URL = "http://api.football-data.org/v4/competitions/WC/matches"
HEADERS = {"X-Auth-Token": API_KEY}

# Lista perfecta a celor 48 de echipe
teams_2026 = {
    "Algeria": "ALG", "Argentina": "ARG", "Australia": "AUS", "Austria": "AUT", 
    "Belgium": "BEL", "Bosnia and Herzegovina": "BIH", "Brazil": "BRA", "Canada": "CAN", 
    "Cape Verde": "CPV", "Colombia": "COL", "Congo DR": "COD", "Croatia": "CRO", 
    "Curaçao": "CUW", "Czechia": "CZE", "Ecuador": "ECU", "Egypt": "EGY", 
    "England": "ENG", "France": "FRA", "Germany": "GER", "Ghana": "GHA", 
    "Haiti": "HAI", "Iran": "IRN", "Iraq": "IRQ", "Ivory Coast": "CIV", 
    "Japan": "JPN", "Jordan": "JOR", "Mexico": "MEX", "Morocco": "MAR", 
    "Netherlands": "NED", "New Zealand": "NZL", "Norway": "NOR", "Panama": "PAN", 
    "Paraguay": "PAR", "Portugal": "POR", "Qatar": "QAT", "Saudi Arabia": "KSA", 
    "Scotland": "SCO", "Senegal": "SEN", "South Africa": "RSA", "South Korea": "KOR", 
    "Spain": "ESP", "Sweden": "SWE", "Switzerland": "SUI", "Tunisia": "TUN", 
    "Turkiye": "TUR", "United States": "USA", "Uruguay": "URU", "Uzbekistan": "UZB"
}

# Aliasuri pentru API
ALIASES = {
    "korea republic": "South Korea",
    "usa": "United States",
    "ir iran": "Iran",
    "cote d'ivoire": "Ivory Coast",
    "dr congo": "Congo DR",
    "congo democratic republic": "Congo DR",
    "bosnia & herzegovina": "Bosnia and Herzegovina",
    "cabo verde": "Cape Verde",
    "bosnia-herzegovina": "Bosnia and Herzegovina",
    "cape verde islands": "Cape Verde",
    "turkey": "Turkiye",
}

def normalizeaza(nume):
    nume = unicodedata.normalize('NFKD', nume)
    nume = ''.join(c for c in nume if not unicodedata.combining(c))
    return nume.lower().strip()

def get_db_team_name(api_name):
    norm = normalizeaza(api_name)
    # Verifica in aliasuri
    if norm in ALIASES.keys():
        return ALIASES[norm]
    # Verifica direct in lista ta (ignorand majusculele/diacriticele)
    for db_name in teams_2026.keys():
        if normalizeaza(db_name) == norm:
            return db_name
    return api_name

def build_perfect_database():
    conn = sqlite3.connect('world_cup.db')
    cursor = conn.cursor()
    
    print("🧹 1. Se șterg datele vechi...")
    cursor.execute("DROP TABLE IF EXISTS Fixtures")
    cursor.execute("DROP TABLE IF EXISTS Teams")
    
    print("🏗️ 2. Se construiesc tabelele noi, curate...")
    cursor.execute('''
        CREATE TABLE Teams (
            team_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            code TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE Fixtures (
            fixture_id INTEGER PRIMARY KEY,
            home_team_id INTEGER,
            away_team_id INTEGER,
            home_goals INTEGER,
            away_goals INTEGER,
            status TEXT,
            match_date TEXT,
            FOREIGN KEY (home_team_id) REFERENCES Teams (team_id),
            FOREIGN KEY (away_team_id) REFERENCES Teams (team_id)
        )
    ''')
    
    print("🌟 3. Se adaugă cele 48 de echipe cu tot cu coduri...")
    for name, code in teams_2026.items():
        cursor.execute("INSERT INTO Teams (name, code) VALUES (?, ?)", (name, code))
    
    conn.commit()
    
    print("⚽ 4. Se descarcă meciurile oficiale 2026 de la API...")
    response = requests.get(URL, headers=HEADERS)
    if response.status_code != 200:
        print(f"Eroare API: {response.status_code}")
        return
        
    matches_data = response.json().get('matches', [])
    meciuri = 0
    meciuri_ratate = set()
    
    for match in matches_data:
        if match['status'] == 'FINISHED':
            # Mapăm numele de la API la numele din baza ta de date
            home_team = get_db_team_name(match['homeTeam']['name'])
            away_team = get_db_team_name(match['awayTeam']['name'])
            match_date = match['utcDate']
            
            if 'fullTime' in match['score'] and match['score']['fullTime']['home'] is not None:
                home_goals = match['score']['fullTime']['home']
                away_goals = match['score']['fullTime']['away']
            else:
                home_goals = match['score']['regularTime']['home']
                away_goals = match['score']['regularTime']['away']
            
            cursor.execute("SELECT team_id FROM Teams WHERE name = ?", (home_team,))
            h_res = cursor.fetchone()
            cursor.execute("SELECT team_id FROM Teams WHERE name = ?", (away_team,))
            a_res = cursor.fetchone()
            
            if h_res and a_res:
                cursor.execute("""
                    INSERT INTO Fixtures (home_team_id, away_team_id, home_goals, away_goals, status, match_date)
                    VALUES (?, ?, ?, ?, 'FT', ?)
                """, (h_res[0], a_res[0], home_goals, away_goals, match_date))
                meciuri += 1
            else:
                if not h_res: meciuri_ratate.add(match['homeTeam']['name'])
                if not a_res: meciuri_ratate.add(match['awayTeam']['name'])
                
    conn.commit()
    conn.close()
    
    print(f"\n✅ GATA! Baza ta de date este acum impecabilă!")
    print(f"Conține exact 48 de echipe și {meciuri} meciuri (cu tot cu data calendaristică).")
    
    if meciuri_ratate:
        print(f"⚠️ Atenție, echipe ignorate (verifică ALIASES): {meciuri_ratate}")

if __name__ == "__main__":
    build_perfect_database()