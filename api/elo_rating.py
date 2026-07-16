import sqlite3
from datafc import eloratings

DB_NAME = "world_cup.db"

# Coduri datafc -> coduri FIFA din baza ta
CODE_MAP = {
    "AR": "ARG",
    "DZ": "ALG",
    "AU": "AUS",
    "AT": "AUT",
    "BE": "BEL",
    "BA": "BIH",
    "BR": "BRA",
    "CA": "CAN",
    "CV": "CPV",
    "CO": "COL",
    "CG": "COD",
    "HR": "CRO",
    "CW": "CUW",
    "CZ": "CZE",
    "DK": "DEN",
    "EC": "ECU",
    "EN": "ENG",
    "FR": "FRA",
    "DE": "GER",
    "GH": "GHA",
    "IR": "IRN",
    "IT": "ITA",
    "JP": "JPN",
    "KR": "KOR",
    "MA": "MAR",
    "MX": "MEX",
    "NL": "NED",
    "NZ": "NZL",
    "NG": "NGA",
    "NO": "NOR",
    "PA": "PAN",
    "PE": "PER",
    "PL": "POL",
    "PT": "POR",
    "QA": "QAT",
    "SA": "KSA",
    "RS": "SRB",
    "SN": "SEN",
    "ES": "ESP",
    "CH": "SUI",
    "TN": "TUN",
    "TR": "TUR",
    "UA": "UKR",
    "US": "USA",
    "UY": "URU",
    "VE": "VEN",
    "CI": "CIV",
    "PY": "PAR",   # Paraguay
    "SC": "SCO",   # Scotland
    "ZA": "RSA",   # South Africa
    "SE": "SWE",   # Sweden
    "UZ": "UZB",   # Uzbekistan
    "EG": "EGY",
    "HT": "HAI",
    "IQ": "IRQ",
    "JO": "JOR",
}

# Descarcă ratingurile Elo
df = eloratings.world_ranking_data()
#print(sorted(df["country"].unique()))

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Creează coloana dacă nu există
try:
    cursor.execute("""
        ALTER TABLE Teams
        ADD COLUMN elo_rating INTEGER
    """)
    print("✓ Coloana elo_rating a fost creată.")
except sqlite3.OperationalError:
    print("✓ Coloana elo_rating există deja.")

updated = 0

for _, row in df.iterrows():

    code2 = row["country"]

    if code2 not in CODE_MAP:
        continue

    code3 = CODE_MAP[code2]
    elo = int(row["elo"])

    cursor.execute("""
        UPDATE Teams
        SET elo_rating = ?
        WHERE code = ?
    """, (elo, code3))

    if cursor.rowcount > 0:
        updated += 1
        print(f"{code3} -> {elo}")

conn.commit()
conn.close()

print(f"\nAu fost actualizate {updated} echipe.")