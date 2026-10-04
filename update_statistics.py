import os
import requests
import django
import time

from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sports_project.settings")
django.setup()

from api.models import Match


API_URL = "https://v3.football.api-sports.io"
API_KEY = os.getenv("API_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

MAX_REQUESTS = 100


def get_statistics(fixture_id):
    url = f"{API_URL}/fixtures/statistics"

    params = {
        "fixture": fixture_id
    }

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30
    )

    print("Status code:", response.status_code)

    if response.status_code != 200:
        print("Eroare API:")
        print(response.text)
        return []
    if response.status_code == 429:
            return None

    data = response.json()

    if data.get("errors"):
        print("API errors:")
        print(data["errors"])
        return []

    return data.get("response", [])


def extract_statistics(statistics):
    """
    Transformă lista de statistici primită de la API
    într-un dicționar mai ușor de folosit.
    """

    result = {}

    for statistic in statistics:
        statistic_type = statistic["type"]
        value = statistic["value"]

        result[statistic_type] = value

    return result


def convert_percentage(value):
    """
    Transformă '56%' în 56.
    Dacă valoarea lipsește, returnează None.
    """

    if value is None:
        return None

    if isinstance(value, str) and value.endswith("%"):
        return int(value[:-1])

    return value


def update_match(match, fixture):
    """
    Actualizează statisticile unui meci din baza de date.
    """

    fixture_id = fixture["fixture"]["id"]

    home_team_name = fixture["teams"]["home"]["name"]
    away_team_name = fixture["teams"]["away"]["name"]

    home_stats = None
    away_stats = None

    for team_data in fixture.get("statistics", []):
        team_name = team_data["team"]["name"]
        stats = extract_statistics(team_data["statistics"])

        if team_name == home_team_name:
            home_stats = stats

        elif team_name == away_team_name:
            away_stats = stats

    if home_stats is None or away_stats is None:
        print(f"Nu am gasit statisticile pentru fixture {fixture_id}")
        return False

    match.home_shots_on_goal = home_stats.get("Shots on Goal")
    match.away_shots_on_goal = away_stats.get("Shots on Goal")

    match.home_shots_off_goal = home_stats.get("Shots off Goal")
    match.away_shots_off_goal = away_stats.get("Shots off Goal")

    match.home_total_shots = home_stats.get("Total Shots")
    match.away_total_shots = away_stats.get("Total Shots")

    match.home_corners = home_stats.get("Corner Kicks")
    match.away_corners = away_stats.get("Corner Kicks")

    match.home_possession = convert_percentage(
        home_stats.get("Ball Possession")
    )
    match.away_possession = convert_percentage(
        away_stats.get("Ball Possession")
    )

    match.home_goalkeeper_saves = home_stats.get("Goalkeeper Saves")
    match.away_goalkeeper_saves = away_stats.get("Goalkeeper Saves")

    match.home_fouls = home_stats.get("Fouls")
    match.away_fouls = away_stats.get("Fouls")

    match.home_offsides = home_stats.get("Offsides")
    match.away_offsides = away_stats.get("Offsides")

    match.home_yellow_cards = home_stats.get("Yellow Cards")
    match.away_yellow_cards = away_stats.get("Yellow Cards")

    match.home_red_cards = home_stats.get("Red Cards")
    match.away_red_cards = away_stats.get("Red Cards")

    match.save()

    return True


def main():

    if not API_KEY:
        print("Lipseste API_KEY din .env")
        return

    matches = list(
        Match.objects
        .select_related("home_team", "away_team")
        .exclude(fixture_id__isnull=True)
        .filter(home_total_shots__isnull=True)
        .order_by("fixture_id")[:MAX_REQUESTS]
    )

    print(f"Meciuri de actualizat: {len(matches)}")

    updated_matches = 0

    for index, match in enumerate(matches, start=1):

        print()
        print(
            f"[{index}/{len(matches)}] "
            f"{match.home_team.name} - {match.away_team.name}"
        )

        statistics = get_statistics(match.fixture_id)

        if statistics is None:
            break

        if not statistics:
            print("Nu am primit statistici.")
            continue

        fixture_data = {
            "fixture": {
                "id": match.fixture_id
            },
            "teams": {
                "home": {
                    "name": match.home_team.name
                },
                "away": {
                    "name": match.away_team.name
                }
            },
            "statistics": statistics
        }

        if update_match(match, fixture_data):
            updated_matches += 1
            print("Statistici salvate.")
        if index % 10 == 0 and index < len(matches):
            print("Au fost procesate 10 request-uri. Astept 60 de secunde...")
            time.sleep(60)

    print()
    print("===================================")
    print("UPDATE TERMINAT!")
    print(f"Meciuri actualizate: {updated_matches}")
    print("===================================")


if __name__ == "__main__":
    main()