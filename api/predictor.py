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

def calculate_team_stats(cursor, team_name, target_date=None):
    cursor.execute("SELECT team_id FROM Teams WHERE name = ?", (team_name,))
    result = cursor.fetchone()
    if not result:
        return None
    team_id = result[0]
    
    # Am adăugat coloana 'stage' în SELECT
    if target_date:
        query = '''SELECT home_goals, away_goals, home_team_id, stage 
                   FROM Fixtures 
                   WHERE (home_team_id= ? OR away_team_id = ?) 
                   AND status IN ('FT', 'AET', 'PEN') 
                   AND match_date < ?
                   ORDER BY match_date DESC LIMIT 5'''
        cursor.execute(query, (team_id, team_id, target_date))
    else:
        query = '''SELECT home_goals, away_goals, home_team_id, stage 
                   FROM Fixtures 
                   WHERE (home_team_id= ? OR away_team_id = ?) 
                   AND status IN ('FT', 'AET', 'PEN')
                   ORDER BY match_date DESC LIMIT 5'''
        cursor.execute(query, (team_id, team_id))
        
    matches = cursor.fetchall()
    
    if len(matches) == 0:
        return None
        
    goals_scored = 0
    goals_conceded = 0
    
    for match in matches:
        home_goals, away_goals, home_team_id, stage = match
        
        # --- LOGICA DE NORMALIZARE ISTORICĂ ---
        if stage == 'THIRD_PLACE':
            factor = 1.35
        elif stage == 'FINAL':
            factor = 0.90
        elif stage in ['LAST_16', 'QUARTER_FINALS', 'SEMI_FINALS']:
            factor = 0.95
        else:
            factor = 1.0 # GROUP_STAGE sau altele
            
        # „Dezumflăm” sau „umflăm” golurile brute pe baza dificultății
        norm_home_goals = home_goals / factor
        norm_away_goals = away_goals / factor

        if home_team_id == team_id:
            # Păstrăm limita de max 3 goluri luate în calcul, dar aplicată pe valoarea normalizată
            goals_scored += min(norm_home_goals, 3)
            goals_conceded += min(norm_away_goals, 3)
        else:
            goals_scored += min(norm_away_goals, 3)
            goals_conceded += min(norm_home_goals, 3)
            
    return {
        "matches_played": len(matches),
        "average_scored": goals_scored / len(matches),
        "average_conceded": goals_conceded / len(matches)
    }

def poisson_probability(lmbda, k):
    return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)

def predict_match(team_A, team_B, match_date=None, comp_type="World Cup",manual_stage=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Obținem ID-urile echipelor
    cursor.execute("SELECT team_id FROM Teams WHERE name = ?", (team_A,))
    res_A = cursor.fetchone()
    cursor.execute("SELECT team_id FROM Teams WHERE name = ?", (team_B,))
    res_B = cursor.fetchone()
    
    if not res_A or not res_B:
        conn.close()
        return f"Eroare: Nu am putut găsi echipele '{team_A}' sau '{team_B}' în baza de date."
        
    tA_id, tB_id = res_A[0], res_B[0]
    
    # --- AUTO-DETECȚIE FAZĂ MECI (STAGE) ---
    # Căutăm meciul direct în baza de date (fie la data cerută pentru backtesting, fie meciul viitor 'NS')
    if manual_stage and manual_stage != "Auto":
        match_stage = manual_stage
    else:
        if match_date:
            cursor.execute('''SELECT stage FROM Fixtures 
                          WHERE ((home_team_id = ? AND away_team_id = ?) OR (home_team_id = ? AND away_team_id = ?))
                          AND match_date = ? LIMIT 1''', (tA_id, tB_id, tB_id, tA_id, match_date))
        else:
            cursor.execute('''SELECT stage FROM Fixtures 
                          WHERE ((home_team_id = ? AND away_team_id = ?) OR (home_team_id = ? AND away_team_id = ?))
                          AND status = 'NS' LIMIT 1''', (tA_id, tB_id, tB_id, tA_id))
    
        stage_result = cursor.fetchone()
        match_stage = stage_result[0] if stage_result else 'REGULAR'

    # --- CALCUL MEDIA TURNEULUI ---
    if match_date:
        cursor.execute("SELECT AVG(home_goals + away_goals) / 2 FROM Fixtures WHERE status IN ('FT', 'AET', 'PEN') AND match_date < ?", (match_date,))
    else:
        cursor.execute("SELECT AVG(home_goals + away_goals) / 2 FROM Fixtures WHERE status IN ('FT', 'AET', 'PEN')")
        
    result_avg = cursor.fetchone()[0]
    tournament_avg_goals = result_avg if result_avg is not None else 1.0
    
    # --- CALCUL STATISTICI ECHIPE (CU NORMALIZARE) ---
    stats_A = calculate_team_stats(cursor, team_A, target_date=match_date)
    stats_B = calculate_team_stats(cursor, team_B, target_date=match_date)
    
    if not stats_A or not stats_B:
        conn.close()
        return f"Eroare: Lipsesc meciurile anterioare pentru {team_A} sau {team_B}."
    
    pondere_medie = 3.0
    medie_atac_A = (stats_A['average_scored'] * stats_A['matches_played'] + tournament_avg_goals * pondere_medie) / (stats_A['matches_played'] + pondere_medie)
    medie_aparare_B = (stats_B['average_conceded'] * stats_B['matches_played'] + tournament_avg_goals * pondere_medie) / (stats_B['matches_played'] + pondere_medie)
    
    medie_atac_B = (stats_B['average_scored'] * stats_B['matches_played'] + tournament_avg_goals * pondere_medie) / (stats_B['matches_played'] + pondere_medie)
    medie_aparare_A = (stats_A['average_conceded'] * stats_A['matches_played'] + tournament_avg_goals * pondere_medie) / (stats_A['matches_played'] + pondere_medie)

    attack_A = medie_atac_A / tournament_avg_goals
    defense_B = medie_aparare_B / tournament_avg_goals
    attack_B = medie_atac_B / tournament_avg_goals
    defense_A = medie_aparare_A / tournament_avg_goals

    # --- CITIRE ELO ---
    cursor.execute("SELECT elo_rating FROM Teams WHERE team_id = ?", (tA_id,))
    elo_A = cursor.fetchone()[0]
    cursor.execute("SELECT elo_rating FROM Teams WHERE team_id = ?", (tB_id,))
    elo_B = cursor.fetchone()[0]

    elo_diff = elo_A - elo_B
    elo_factor = pow(10, elo_diff / 8000)

    attack_A *= elo_factor
    attack_B /= elo_factor
    
    xg_A_initial = attack_A * defense_B * tournament_avg_goals
    xg_B_initial = attack_B * defense_A * tournament_avg_goals

    # --- APLICAREA MULTIPLICATORULUI DE CONTEXT (PENTRU MECIUL ACTUAL) ---
    if comp_type == "Friendly":
        xg_A_initial *= 1.25
        xg_B_initial *= 1.25
    
    if match_stage == 'THIRD_PLACE':
        xg_A_initial *= 1.35
        xg_B_initial *= 1.35
    elif match_stage == 'FINAL':
        xg_A_initial *= 0.90
        xg_B_initial *= 0.90
    elif match_stage in ['LAST_16', 'QUARTER_FINALS', 'SEMI_FINALS']:
        xg_A_initial *= 0.95
        xg_B_initial *= 0.95

    # Clamp
    xg_A = max(0.4, min(xg_A_initial, 3))
    xg_B = max(0.4, min(xg_B_initial, 3))

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
    # print("========================================")
    # print("      TESTARE SFERTURI DE FINALĂ        ")
    # print("========================================\n")
    
    # # 1. Franța - Maroc (Flashscore: 09.07 23:00 / UTC Start: 20:00)
    # print(">>> FRANȚA vs MAROC")
    # print(predict_match("France", "Morocco", "2026-07-09T18:00:00Z"))
    
    # # 2. Spania - Belgia (Flashscore: 10.07 22:00 / UTC Start: 19:00)
    # print(">>> SPANIA vs BELGIA")
    # print(predict_match("Spain", "Belgium", "2026-07-10T17:00:00Z"))
    
    # # 3. Norvegia - Anglia (Flashscore: 12.07 00:00 / UTC Start: 11.07 21:00)
    # print(">>> NORVEGIA vs ANGLIA")
    # print(predict_match("Norway", "England", "2026-07-11T19:00:00Z"))
    
    # # 4. Argentina - Elveția (Flashscore: 12.07 04:00 / UTC Start: 12.07 01:00)
    # print(">>> ARGENTINA vs ELVEȚIA")
    # print(predict_match("Argentina", "Switzerland", "2026-07-11T23:00:00Z"))
    

    # print("\n========================================")
    # print("           TESTARE SEMIFINALE           ")
    # print("========================================\n")
    
    # # 5. Franța - Spania (Flashscore: 14.07 22:00 / UTC Start: 19:00)
    # print(">>> FRANȚA vs SPANIA")
    # print(predict_match("France", "Spain", "2026-07-14T17:00:00Z"))
    
    # # 6. Anglia - Argentina (Flashscore: 15.07 22:00 / UTC Start: 19:00)
    # print(">>> ANGLIA vs ARGENTINA")
    # print(predict_match("England", "Argentina", "2026-07-15T17:00:00Z"))
    #print(predict_match("Spain", "Argentina"))
    print(predict_match("France", "England"))
