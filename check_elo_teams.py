import csv
import sqlite3


DB_PATH = "club_football.db"
ELO_FILE = "data/EloRatings.csv"


def get_database_teams():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name
        FROM api_team
        ORDER BY name
    """)

    teams = [row[0] for row in cursor.fetchall()]

    conn.close()

    return teams


def get_elo_teams():
    teams = set()

    with open(ELO_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            teams.add(row["club"])

    return sorted(teams)


def main():
    database_teams = get_database_teams()
    elo_teams = get_elo_teams()

    elo_teams_set = set(elo_teams)

    print("=== ECHIPE API-FOOTBALL ===")
    for team in database_teams:
        print(team)

    print("\n=== ECHIPE API-FOOTBALL FARA CORESPONDENT IN ELO ===")

    for team in database_teams:
        if team not in elo_teams_set:
            print(team)

    print("\n=== ECHIPE ELO CARE NU SUNT IN API-FOOTBALL ===")

    database_teams_set = set(database_teams)

    for team in elo_teams:
        if team not in database_teams_set:
            print(team)


if __name__ == "__main__":
    main()