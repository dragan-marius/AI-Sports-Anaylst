import requests
import sqlite3
import os
import unicodedata
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

URL = "http://api.football-data.org/v4/competitions/WC/matches"
HEADERS = {"X-Auth-Token": API_KEY}

# Nume alternative folosite de football-data.org care NU se rezolvă doar
# prin eliminarea diacriticelor (sunt cuvinte complet diferite, nu doar
# ortografie). Dacă vezi în log un meci ratat cu un nume nou, adaugă-l aici.
ALIASES = {
    "korea republic": "south korea",
    "usa": "united states",
    "ir iran": "iran",
    "cote d'ivoire": "ivory coast",
    "dr congo": "congo dr",
    "congo democratic republic": "congo dr",
    "bosnia & herzegovina": "bosnia and herzegovina",
    "cabo verde": "cape verde",
    "bosnia-herzegovina": "bosnia and herzegovina",
    "cape verde islands": "cape verde",
    "turkey": "turkiye",
}


def normalizeaza(nume):
    nume = unicodedata.normalize('NFKD', nume)
    nume = ''.join(c for c in nume if not unicodedata.combining(c))
    return nume.lower().strip()


def gaseste_team_id(cursor, teams_by_normalized, nume_api):
    normalizat = normalizeaza(nume_api)

    if normalizat in teams_by_normalized:
        return teams_by_normalized[normalizat], None

    if normalizat in ALIASES:
        alias_normalizat = normalizeaza(ALIASES[normalizat])
        if alias_normalizat in teams_by_normalized:
            return teams_by_normalized[alias_normalizat], None

    return None, nume_api


def sync_new_matches():
    conn = sqlite3.connect('world_cup.db')
    cursor = conn.cursor()

    cursor.execute("SELECT team_id, name FROM Teams")
    teams_by_normalized = {normalizeaza(name): tid for tid, name in cursor.fetchall()}

    print("1. Se descarcă meciurile de la API...")
    response = requests.get(URL, headers=HEADERS)
    if response.status_code != 200:
        print(f"Eroare la conectare API: {response.status_code}")
        conn.close()
        return

    matches_data = response.json().get('matches', [])

    meciuri_adaugate = 0
    nume_neidentificate = set()

    for match in matches_data:
        if match['status'] != 'FINISHED':
            continue

        home_name_api = match['homeTeam']['name']
        away_name_api = match['awayTeam']['name']
        match_date = match['utcDate']

        if 'fullTime' in match['score'] and match['score']['fullTime']['home'] is not None:
            home_goals = match['score']['fullTime']['home']
            away_goals = match['score']['fullTime']['away']
        else:
            home_goals = match['score']['regularTime']['home']
            away_goals = match['score']['regularTime']['away']

        home_id, missing_home = gaseste_team_id(cursor, teams_by_normalized, home_name_api)
        away_id, missing_away = gaseste_team_id(cursor, teams_by_normalized, away_name_api)

        if missing_home:
            nume_neidentificate.add(missing_home)
        if missing_away:
            nume_neidentificate.add(missing_away)

        if home_id is None or away_id is None:
            continue

        cursor.execute(
            "SELECT 1 FROM Fixtures WHERE home_team_id = ? AND away_team_id = ?",
            (home_id, away_id)
        )
        if cursor.fetchone():
            continue

        cursor.execute(
            """INSERT INTO Fixtures (home_team_id, away_team_id, home_goals, away_goals, status, match_date)
               VALUES (?, ?, ?, ?, 'FT')""",
            (home_id, away_id, home_goals, away_goals, match_date)
        )
        meciuri_adaugate += 1
        print(f"✅ Adăugat: {home_name_api} {home_goals} - {away_goals} {away_name_api}")

    conn.commit()
    conn.close()

    print(f"\n🚀 Gata! {meciuri_adaugate} meciuri noi adăugate.")

    if nume_neidentificate:
        print("\n⚠️  Nume de echipe primite de la API care NU au putut fi mapate la baza ta de date:")
        for nume in sorted(nume_neidentificate):
            print(f"   - '{nume}'")
        print("   Adaugă-le în dicționarul ALIASES din acest script (nume_api -> nume_din_baza_ta),")
        print("   apoi rulează din nou scriptul ca să prinzi și meciurile lor.")


if __name__ == "__main__":
    sync_new_matches()