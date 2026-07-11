import sqlite3
import math

def get_db_connection():
    return sqlite3.connect('world_cup.db')

def calcul_corectie_tau(xg_A, xg_B, goluri_A, goluri_B, rho=-0.12):
    # Corectează probabilitățile pentru scorurile mici și egale
    if goluri_A == 0 and goluri_B == 0:
        return max(0, 1 - (xg_A * xg_B * rho))
    elif goluri_A == 1 and goluri_B == 0:
        return max(0, 1 + (xg_A * rho))
    elif goluri_A == 0 and goluri_B == 1:
        return max(0, 1 + (xg_B * rho))
    elif goluri_A == 1 and goluri_B == 1:
        return max(0, 1 - rho)
    return 1.0

def calculate_team_stats(cursor, team_name):
    cursor.execute("SELECT team_id FROM Teams WHERE name = ?", (team_name,))
    result = cursor.fetchone()
    if not result:
        return None
    team_id = result[0]
    cursor.execute('''SELECT home_goals, away_goals, home_team_id FROM fixtures WHERE (home_team_id= ? OR away_team_id = ?) AND status IN ('FT', 'AET', 'PEN') ''', (team_id, team_id))
    matches = cursor.fetchall()
    if len(matches) == 0:
        return None
    goals_scored = 0
    goals_conceded = 0
    for match in matches:
        home_goals, away_goals, home_team_id = match
        if home_team_id == team_id:
            goals_scored += min(home_goals, 3)
            goals_conceded += min(away_goals, 3)
        else:
            goals_scored += min(away_goals, 3)
            goals_conceded += min(home_goals, 3)
    return {
        "matches_played": len(matches),
        "average_scored": goals_scored / len(matches),
        "average_conceded": goals_conceded / len(matches)
    }

def poisson_probability(lmbda, k):
    return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)

def predict_match(team_A, team_B):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT AVG(home_goals + away_goals) / 2 FROM Fixtures WHERE status IN ('FT', 'AET', 'PEN') ")
    tournament_avg_goals = cursor.fetchone()[0]
    
    stats_A = calculate_team_stats(cursor, team_A)
    stats_B = calculate_team_stats(cursor, team_B)
    
    if not stats_A or not stats_B:
        conn.close()
        return f"Eroare: Nu am putut găsi echipele '{team_A}' sau '{team_B}' în baza de date. Cere-i utilizatorului să verifice numele în engleză."
    
    pondere_medie = 0.5
    # Netezim mediile de atac si aparare
    medie_atac_A = (stats_A['average_scored'] * stats_A['matches_played'] + tournament_avg_goals * pondere_medie) / (stats_A['matches_played'] + pondere_medie)
    medie_aparare_B = (stats_B['average_conceded'] * stats_B['matches_played'] + tournament_avg_goals * pondere_medie) / (stats_B['matches_played'] + pondere_medie)
    
    medie_atac_B = (stats_B['average_scored'] * stats_B['matches_played'] + tournament_avg_goals * pondere_medie) / (stats_B['matches_played'] + pondere_medie)
    medie_aparare_A = (stats_A['average_conceded'] * stats_A['matches_played'] + tournament_avg_goals * pondere_medie) / (stats_A['matches_played'] + pondere_medie)

    # Calculam forta relativa fata de media turneului
    attack_A = medie_atac_A / tournament_avg_goals
    defense_B = medie_aparare_B / tournament_avg_goals
    attack_B = medie_atac_B / tournament_avg_goals
    defense_A = medie_aparare_A / tournament_avg_goals

    xg_A_initial = attack_A * defense_B * tournament_avg_goals
    xg_B_initial = attack_B * defense_A * tournament_avg_goals
    # target_total = 2.65 
    # expected_total_goals = xg_A_initial + xg_B_initial
    # if expected_total_goals > target_total:
    #     scale_factor = target_total / expected_total_goals
    #     xg_A = xg_A_initial * scale_factor
    #     xg_B = xg_B_initial * scale_factor
    # else:
    xg_A = xg_A_initial
    xg_B = xg_B_initial
    
    xg_A = max(0.4, min(xg_A, 3))
    xg_B = max(0.4, min(xg_B, 3))


    prob_A_wins = 0
    prob_B_wins = 0
    prob_draw = 0
    max_goals_team = 10
    prob_under = [0.0] * (max_goals_team * 2 + 1)
    prob_over = [0.0] * (max_goals_team * 2 + 1)

    for goals_A in range(max_goals_team):
        for goals_B in range(max_goals_team):
            prob_score = poisson_probability(xg_A, goals_A) * poisson_probability(xg_B, goals_B)
            prob_score*= calcul_corectie_tau(xg_A, xg_B,goals_A,goals_B)
            if goals_A > goals_B:
                prob_A_wins += prob_score
            elif goals_B > goals_A:
                prob_B_wins += prob_score
            else:
                prob_draw += prob_score
            goals = goals_A + goals_B
            for i in range(goals, len(prob_under)):
                prob_under[i] += prob_score
    conn.close()

    margin = 1.05
    win_team_A = (1 / max(prob_A_wins, 0.001))/margin
    win_team_B = (1 / max(prob_B_wins, 0.001))/margin
    draw = (1 / max(prob_draw, 0.001))/margin

    rez = f"--- PREDICȚIE MATEMATICĂ: {team_A} vs {team_B} ---\n"
    rez += f"Expected Goals (xG): {team_A} ({xg_A:.2f}) - {team_B} ({xg_B:.2f})\n"
    rez += f"Cote victorie {team_A}: {win_team_A:.2f}\n"
    rez += f"Cote victorie {team_B}: {win_team_B:.2f}\n"
    rez += f"Cote egalitate: {draw:.2f}\n\n"
    rez += "--- COTE SUB/PESTE ---\n"

    for i in range(len(prob_under)):
        prob_over[i] = 1 - prob_under[i]
        
    for i in range(0, 8):
        under = 1 / max(prob_under[i], 0.001)
        over = 1 / max(prob_over[i], 0.001)
        rez += f"Sub {i}.5: {under:.2f} | Peste {i}.5: {over:.2f}\n"

    return rez

if __name__ == "__main__":
    print(predict_match("France", "Morocco"))
    print(predict_match("Spain", "Belgium"))
    print(predict_match("England", "Norway"))
    print(predict_match("Switzerland", "Argentina"))