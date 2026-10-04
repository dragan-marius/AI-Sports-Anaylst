import sqlite3


WINDOWS = (5, 10, 20)


def get_db_connection():
    return sqlite3.connect("club_football.db")


def get_team_matches(cursor, team_id, limit=10, target_date=None, location=None):

    if target_date:

        if location is None:
            query = """
                SELECT
                    date,
                    home_team_id,
                    away_team_id,
                    home_goals,
                    away_goals,
                    home_shots_on_goal,
                    away_shots_on_goal,
                    home_shots_off_goal,
                    away_shots_off_goal,
                    home_total_shots,
                    away_total_shots,
                    home_corners,
                    away_corners,
                    home_possession,
                    away_possession,
                    home_goalkeeper_saves,
                    away_goalkeeper_saves,
                    home_fouls,
                    away_fouls,
                    home_offsides,
                    away_offsides,
                    home_yellow_cards,
                    away_yellow_cards,
                    home_red_cards,
                    away_red_cards
                FROM api_match
                WHERE (home_team_id = ? OR away_team_id = ?)
                AND status IN ('FT', 'AET', 'PEN')
                AND date < ?
                ORDER BY date DESC
                LIMIT ?
            """

            params = (team_id, team_id, target_date, limit)

        elif location == "home":
            query = """
                SELECT
                    date,
                    home_team_id,
                    away_team_id,
                    home_goals,
                    away_goals,
                    home_shots_on_goal,
                    away_shots_on_goal,
                    home_shots_off_goal,
                    away_shots_off_goal,
                    home_total_shots,
                    away_total_shots,
                    home_corners,
                    away_corners,
                    home_possession,
                    away_possession,
                    home_goalkeeper_saves,
                    away_goalkeeper_saves,
                    home_fouls,
                    away_fouls,
                    home_offsides,
                    away_offsides,
                    home_yellow_cards,
                    away_yellow_cards,
                    home_red_cards,
                    away_red_cards
                FROM api_match
                WHERE home_team_id = ?
                AND status IN ('FT', 'AET', 'PEN')
                AND date < ?
                ORDER BY date DESC
                LIMIT ?
            """

            params = (team_id, target_date, limit)

        elif location == "away":
            query = """
                SELECT
                    date,
                    home_team_id,
                    away_team_id,
                    home_goals,
                    away_goals,
                    home_shots_on_goal,
                    away_shots_on_goal,
                    home_shots_off_goal,
                    away_shots_off_goal,
                    home_total_shots,
                    away_total_shots,
                    home_corners,
                    away_corners,
                    home_possession,
                    away_possession,
                    home_goalkeeper_saves,
                    away_goalkeeper_saves,
                    home_fouls,
                    away_fouls,
                    home_offsides,
                    away_offsides,
                    home_yellow_cards,
                    away_yellow_cards,
                    home_red_cards,
                    away_red_cards
                FROM api_match
                WHERE away_team_id = ?
                AND status IN ('FT', 'AET', 'PEN')
                AND date < ?
                ORDER BY date DESC
                LIMIT ?
            """

            params = (team_id, target_date, limit)

        else:
            raise ValueError("location trebuie sa fie None, 'home' sau 'away'")

    else:

        if location is None:
            query = """
                SELECT
                    date,
                    home_team_id,
                    away_team_id,
                    home_goals,
                    away_goals,
                    home_shots_on_goal,
                    away_shots_on_goal,
                    home_shots_off_goal,
                    away_shots_off_goal,
                    home_total_shots,
                    away_total_shots,
                    home_corners,
                    away_corners,
                    home_possession,
                    away_possession,
                    home_goalkeeper_saves,
                    away_goalkeeper_saves,
                    home_fouls,
                    away_fouls,
                    home_offsides,
                    away_offsides,
                    home_yellow_cards,
                    away_yellow_cards,
                    home_red_cards,
                    away_red_cards
                FROM api_match
                WHERE (home_team_id = ? OR away_team_id = ?)
                AND status IN ('FT', 'AET', 'PEN')
                ORDER BY date DESC
                LIMIT ?
            """

            params = (team_id, team_id, limit)

        elif location == "home":
            query = """
                SELECT
                    date,
                    home_team_id,
                    away_team_id,
                    home_goals,
                    away_goals,
                    home_shots_on_goal,
                    away_shots_on_goal,
                    home_shots_off_goal,
                    away_shots_off_goal,
                    home_total_shots,
                    away_total_shots,
                    home_corners,
                    away_corners,
                    home_possession,
                    away_possession,
                    home_goalkeeper_saves,
                    away_goalkeeper_saves,
                    home_fouls,
                    away_fouls,
                    home_offsides,
                    away_offsides,
                    home_yellow_cards,
                    away_yellow_cards,
                    home_red_cards,
                    away_red_cards
                FROM api_match
                WHERE home_team_id = ?
                AND status IN ('FT', 'AET', 'PEN')
                ORDER BY date DESC
                LIMIT ?
            """

            params = (team_id, limit)

        elif location == "away":
            query = """
                SELECT
                    date,
                    home_team_id,
                    away_team_id,
                    home_goals,
                    away_goals,
                    home_shots_on_goal,
                    away_shots_on_goal,
                    home_shots_off_goal,
                    away_shots_off_goal,
                    home_total_shots,
                    away_total_shots,
                    home_corners,
                    away_corners,
                    home_possession,
                    away_possession,
                    home_goalkeeper_saves,
                    away_goalkeeper_saves,
                    home_fouls,
                    away_fouls,
                    home_offsides,
                    away_offsides,
                    home_yellow_cards,
                    away_yellow_cards,
                    home_red_cards,
                    away_red_cards
                FROM api_match
                WHERE away_team_id = ?
                AND status IN ('FT', 'AET', 'PEN')
                ORDER BY date DESC
                LIMIT ?
            """

            params = (team_id, limit)

        else:
            raise ValueError("location trebuie sa fie None, 'home' sau 'away'")

    cursor.execute(query, params)

    return cursor.fetchall()


def calculate_team_stats(matches, team_id):

    if not matches:
        return None

    stats = {
        "matches_played": 0,
        "goals_scored": 0,
        "goals_conceded": 0,
        "shots_on_goal": 0,
        "shots_off_goal": 0,
        "total_shots": 0,
        "corners": 0,
        "possession": 0,
        "goalkeeper_saves": 0,
        "fouls": 0,
        "offsides": 0,
        "yellow_cards": 0,
        "red_cards": 0
    }

    for match in matches:

        (
            date,
            home_team_id,
            away_team_id,
            home_goals,
            away_goals,
            home_shots_on_goal,
            away_shots_on_goal,
            home_shots_off_goal,
            away_shots_off_goal,
            home_total_shots,
            away_total_shots,
            home_corners,
            away_corners,
            home_possession,
            away_possession,
            home_goalkeeper_saves,
            away_goalkeeper_saves,
            home_fouls,
            away_fouls,
            home_offsides,
            away_offsides,
            home_yellow_cards,
            away_yellow_cards,
            home_red_cards,
            away_red_cards
        ) = match

        if home_team_id == team_id:

            goals_scored = home_goals
            goals_conceded = away_goals

            shots_on_goal = home_shots_on_goal
            shots_off_goal = home_shots_off_goal
            total_shots = home_total_shots
            corners = home_corners
            possession = home_possession
            goalkeeper_saves = home_goalkeeper_saves
            fouls = home_fouls
            offsides = home_offsides
            yellow_cards = home_yellow_cards
            red_cards = home_red_cards

        else:

            goals_scored = away_goals
            goals_conceded = home_goals

            shots_on_goal = away_shots_on_goal
            shots_off_goal = away_shots_off_goal
            total_shots = away_total_shots
            corners = away_corners
            possession = away_possession
            goalkeeper_saves = away_goalkeeper_saves
            fouls = away_fouls
            offsides = away_offsides
            yellow_cards = away_yellow_cards
            red_cards = away_red_cards

        stats["matches_played"] += 1
        stats["goals_scored"] += goals_scored or 0
        stats["goals_conceded"] += goals_conceded or 0
        stats["shots_on_goal"] += shots_on_goal or 0
        stats["shots_off_goal"] += shots_off_goal or 0
        stats["total_shots"] += total_shots or 0
        stats["corners"] += corners or 0
        stats["possession"] += possession or 0
        stats["goalkeeper_saves"] += goalkeeper_saves or 0
        stats["fouls"] += fouls or 0
        stats["offsides"] += offsides or 0
        stats["yellow_cards"] += yellow_cards or 0
        stats["red_cards"] += red_cards or 0

    matches_played = stats["matches_played"]

    for key in stats:
        if key != "matches_played":
            stats[key] /= matches_played

    return stats


def calculate_form_stats(cursor, team_id):

    form_stats = {}

    for window in WINDOWS:

        matches = get_team_matches(
            cursor,
            team_id,
            limit=window
        )

        stats = calculate_team_stats(matches, team_id)

        form_stats[window] = stats

    return form_stats


def calculate_attack_defense(form_stats):

    result = {}

    for window, stats in form_stats.items():

        if stats is None:
            result[window] = None
            continue

        attack_strength = (
            0.50 * stats["goals_scored"]
            + 0.30 * stats["shots_on_goal"]
            + 0.20 * stats["total_shots"]
        )

        defense_strength = stats["goals_conceded"]

        result[window] = {
            "attack_strength": attack_strength,
            "defense_strength": defense_strength
        }

    return result


def calculate_home_away_stats(cursor, team_id):

    result = {
        "home": {},
        "away": {}
    }

    for window in WINDOWS:

        home_matches = get_team_matches(
            cursor,
            team_id,
            limit=window,
            location="home"
        )

        away_matches = get_team_matches(
            cursor,
            team_id,
            limit=window,
            location="away"
        )

        home_stats = calculate_team_stats(
            home_matches,
            team_id
        )

        away_stats = calculate_team_stats(
            away_matches,
            team_id
        )

        result["home"][window] = home_stats
        result["away"][window] = away_stats

    return result

def calculate_home_away_attack_defense(home_away_stats):
    result = {
        "home": {},
        "away": {}
    }

    for location in ("home", "away"):
        for window, stats in home_away_stats[location].items():

            if stats is None:
                result[location][window] = None
                continue

            attack_strength = (
                0.50 * stats["goals_scored"]
                + 0.30 * stats["shots_on_goal"]
                + 0.20 * stats["total_shots"]
            )

            defense_strength = stats["goals_conceded"]

            result[location][window] = {
                "attack_strength": attack_strength,
                "defense_strength": defense_strength
            }

    return result


def get_team_elo(cursor, team_id, target_date=None):
    """
    Returneaza cel mai recent Elo al unei echipe.

    target_date:
        - specificat -> ultimul Elo inainte de acea data
        - None -> cel mai recent Elo disponibil
    """

    if target_date is not None:
        cursor.execute("""
            SELECT elo
            FROM api_teamelo
            WHERE team_id = ?
              AND date < ?
            ORDER BY date DESC
            LIMIT 1
        """, (team_id, target_date))
    else:
        cursor.execute("""
            SELECT elo
            FROM api_teamelo
            WHERE team_id = ?
            ORDER BY date DESC
            LIMIT 1
        """, (team_id,))

    result = cursor.fetchone()

    if result is None:
        return None

    return result[0]

def calculate_elo_difference(cursor, home_team_id, away_team_id, target_date=None):
    """
    Calculeaza diferenta Elo dintre echipa gazda si echipa oaspete.
    """

    home_elo = get_team_elo(
        cursor,
        home_team_id,
        target_date
    )

    away_elo = get_team_elo(
        cursor,
        away_team_id,
        target_date
    )

    if home_elo is None or away_elo is None:
        return None

    return {
        "home_elo": home_elo,
        "away_elo": away_elo,
        "elo_difference": home_elo - away_elo
    }


if __name__ == "__main__":

    conn = get_db_connection()
    cursor = conn.cursor()

    # ==========================================
    # TEAM IDS
    # ==========================================

    cursor.execute(
        "SELECT id FROM api_team WHERE name = ?",
        ("Arsenal",)
    )
    arsenal = cursor.fetchone()

    cursor.execute(
        "SELECT id FROM api_team WHERE name = ?",
        ("Liverpool",)
    )
    liverpool = cursor.fetchone()

    if not arsenal or not liverpool:
        print("Una dintre echipe nu a fost gasita.")
        conn.close()
        exit()

    arsenal_id = arsenal[0]
    liverpool_id = liverpool[0]

    print("========================================")
    print("        TEST PREDICTOR")
    print("========================================")

    print(f"Arsenal ID: {arsenal_id}")
    print(f"Liverpool ID: {liverpool_id}")

    # ==========================================
    # ARSENAL - FORM
    # ==========================================

    arsenal_form = calculate_form_stats(
        cursor,
        arsenal_id
    )

    print("\n========================================")
    print("ARSENAL - FORM")
    print("========================================")
    print(arsenal_form)

    # ==========================================
    # LIVERPOOL - FORM
    # ==========================================

    liverpool_form = calculate_form_stats(
        cursor,
        liverpool_id
    )

    print("\n========================================")
    print("LIVERPOOL - FORM")
    print("========================================")
    print(liverpool_form)

    # ==========================================
    # ATTACK / DEFENSE
    # ==========================================

    arsenal_attack_defense = calculate_attack_defense(
        arsenal_form
    )

    liverpool_attack_defense = calculate_attack_defense(
        liverpool_form
    )

    print("\n========================================")
    print("ARSENAL - ATTACK / DEFENSE")
    print("========================================")
    print(arsenal_attack_defense)

    print("\n========================================")
    print("LIVERPOOL - ATTACK / DEFENSE")
    print("========================================")
    print(liverpool_attack_defense)

    # ==========================================
    # HOME / AWAY
    # ==========================================

    arsenal_home_away = calculate_home_away_stats(
        cursor,
        arsenal_id
    )

    liverpool_home_away = calculate_home_away_stats(
        cursor,
        liverpool_id
    )

    print("\n========================================")
    print("ARSENAL - HOME / AWAY")
    print("========================================")
    print(arsenal_home_away)

    print("\n========================================")
    print("LIVERPOOL - HOME / AWAY")
    print("========================================")
    print(liverpool_home_away)

    # ==========================================
    # HOME / AWAY ATTACK / DEFENSE
    # ==========================================

    arsenal_home_away_ad = calculate_home_away_attack_defense(
        arsenal_home_away
    )

    liverpool_home_away_ad = calculate_home_away_attack_defense(
        liverpool_home_away
    )

    print("\n========================================")
    print("ARSENAL - HOME / AWAY ATTACK / DEFENSE")
    print("========================================")
    print(arsenal_home_away_ad)

    print("\n========================================")
    print("LIVERPOOL - HOME / AWAY ATTACK / DEFENSE")
    print("========================================")
    print(liverpool_home_away_ad)

    # ==========================================
    # ELO
    # ==========================================

    elo_difference = calculate_elo_difference(
        cursor,
        arsenal_id,
        liverpool_id
    )

    print("\n========================================")
    print("ARSENAL vs LIVERPOOL - ELO")
    print("========================================")
    print(elo_difference)

    conn.close()