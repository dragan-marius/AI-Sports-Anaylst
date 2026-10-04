import csv
import os
import django
from datetime import datetime, date


# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sports_project.settings")
django.setup()

from api.models import Team, TeamElo


# ============================================================
# CONFIGURATION
# ============================================================

ELO_FILE = "data/EloRatings.csv"

START_DATE = date(2022, 7, 1)
END_DATE = date(2025, 6, 30)


# Numele din EloRatings.csv -> numele din api_team
ELO_NAME_MAPPING = {
    "Man City": "Manchester City",
    "Man United": "Manchester United",
    "Sheffield United": "Sheffield Utd",

    # Nottingham Forest apare sub doua denumiri in CSV
    "Nottm Forest": "Nottingham Forest",
    "Nott'm Forest": "Nottingham Forest",
}


# ============================================================
# HELPERS
# ============================================================

def parse_date(value):
    """
    Converteste data din CSV intr-un obiect date.
    """
    return datetime.strptime(value, "%Y-%m-%d").date()


def get_csv_team_name(elo_team_name):
    """
    Returneaza numele echipei din baza de date pentru
    numele gasit in EloRatings.csv.

    Daca nu exista o exceptie, presupunem ca numele este identic.
    """
    return ELO_NAME_MAPPING.get(elo_team_name, elo_team_name)


def should_import_forest_row(team_name, match_date):
    """
    Rezolva cazul special Nottingham Forest.

    In CSV:
      - pana la sfarsitul lui 2024 apare ca 'Nottm Forest'
      - din 2025 apare ca 'Nott'm Forest'

    Exista si un snapshot duplicat la 2025-06-15 cu vechiul nume,
    pe care il ignoram.
    """

    if team_name == "Nottm Forest":
        return match_date < date(2025, 1, 1)

    if team_name == "Nott'm Forest":
        return match_date >= date(2025, 1, 1)

    return True


# ============================================================
# MAIN IMPORT
# ============================================================

def import_elo():
    print("=== IMPORT ELO ===")

    if not os.path.exists(ELO_FILE):
        print(f"Fisierul nu exista: {ELO_FILE}")
        return

    # --------------------------------------------------------
    # Echipele existente in API-Football / baza noastra
    # --------------------------------------------------------

    db_teams = {
        team.name: team
        for team in Team.objects.all()
    }

    print(f"Echipe gasite in baza de date: {len(db_teams)}")

    imported = 0
    skipped_not_pl = 0
    skipped_date = 0
    skipped_forest_duplicate = 0

    with open(ELO_FILE, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            elo_team_name = row["club"].strip()

            # ------------------------------------------------
            # Data
            # ------------------------------------------------

            try:
                elo_date = parse_date(row["date"])
            except (ValueError, TypeError):
                print(f"Data invalida: {row['date']}")
                continue

            # Doar perioada 2022/23 - 2024/25
            if elo_date < START_DATE or elo_date > END_DATE:
                skipped_date += 1
                continue

            # ------------------------------------------------
            # Cazul special Nottingham Forest
            # ------------------------------------------------

            if elo_team_name in ("Nottm Forest", "Nott'm Forest"):
                if not should_import_forest_row(
                    elo_team_name,
                    elo_date
                ):
                    skipped_forest_duplicate += 1
                    continue

            # ------------------------------------------------
            # Gasim numele echipei din DB
            # ------------------------------------------------

            db_team_name = get_csv_team_name(elo_team_name)

            if db_team_name not in db_teams:
                skipped_not_pl += 1
                continue

            team = db_teams[db_team_name]

            # ------------------------------------------------
            # Elo value
            # ------------------------------------------------

            try:
                elo_value = float(row["elo"])
            except (ValueError, TypeError):
                print(
                    f"Elo invalid pentru {elo_team_name}: "
                    f"{row['elo']}"
                )
                continue

            # ------------------------------------------------
            # Salvare
            # ------------------------------------------------

            _, created = TeamElo.objects.update_or_create(
                team=team,
                date=elo_date,
                defaults={
                    "elo": elo_value
                }
            )

            if created:
                imported += 1

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=== IMPORT TERMINAT ===")
    print(f"Randuri Elo importate/actualizate: {imported}")
    print(f"Randuri ignorate - nu sunt echipe PL: {skipped_not_pl}")
    print(f"Randuri ignorate - in afara perioadei: {skipped_date}")
    print(
        "Randuri Forest ignorate pentru evitarea duplicatelor: "
        f"{skipped_forest_duplicate}"
    )

    print()
    print("=== ECHIPE CU ELO IN DB ===")

    for team in db_teams.values():
        count = TeamElo.objects.filter(team=team).count()

        if count > 0:
            print(f"{team.name}: {count} snapshot-uri")


if __name__ == "__main__":
    import_elo()