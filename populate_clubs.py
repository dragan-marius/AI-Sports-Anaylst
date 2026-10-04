import os
from datetime import datetime

import requests
import django
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sports_project.settings")
django.setup()

from api.models import Team, Competition, Season, Match


API_URL = "https://v3.football.api-sports.io"
API_KEY = os.getenv("API_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

LEAGUE_ID = 39
LEAGUE_NAME = "Premier League"

SEASONS = [2022, 2023, 2024]


def get_matches(season):
    url = f"{API_URL}/fixtures"

    params = {
        "league": LEAGUE_ID,
        "season": season
    }

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30
    )

    if response.status_code != 200:
        print(f"Eroare API pentru sezonul {season}:")
        print(response.status_code)
        print(response.text)
        return []

    data = response.json()

    if data.get("errors"):
        print(f"Eroare API pentru sezonul {season}:")
        print(data["errors"])
        return []

    return data.get("response", [])


def main():

    if not API_KEY:
        print("Lipseste API_KEY din .env")
        return

    competition, _ = Competition.objects.get_or_create(
        name=LEAGUE_NAME
    )

    total_matches = 0

    for season_year in SEASONS:

        season_name = f"{season_year}/{str(season_year + 1)[-2:]}"

        print(f"\nDescarc sezonul {season_name}...")

        matches = get_matches(season_year)

        print(f"Am primit {len(matches)} meciuri.")

        season, _ = Season.objects.get_or_create(
            competition=competition,
            name=season_name
        )

        for match_data in matches:

            fixture = match_data["fixture"]
            teams = match_data["teams"]
            goals = match_data["goals"]
            league = match_data["league"]

            home_data = teams["home"]
            away_data = teams["away"]

            home_team, _ = Team.objects.get_or_create(
                name=home_data["name"],
                defaults={
                    "country": league["country"]
                }
            )

            away_team, _ = Team.objects.get_or_create(
                name=away_data["name"],
                defaults={
                    "country": league["country"]
                }
            )

            match_date = datetime.fromisoformat(
                fixture["date"].replace("Z", "+00:00")
            )

            home_goals = goals.get("home")
            away_goals = goals.get("away")

            Match.objects.update_or_create(
                competition=competition,
                season=season,
                date=match_date,
                home_team=home_team,
                away_team=away_team,
                defaults={
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "stage": league.get(
                        "round",
                        "REGULAR_SEASON"
                    ),
                    "status": fixture["status"]["short"],
                    "fixture_id": fixture["id"],
                }
            )

            total_matches += 1

    print("\n===================================")
    print("IMPORT TERMINAT!")
    print(f"Meciuri procesate: {total_matches}")
    print("===================================")


if __name__ == "__main__":
    main()