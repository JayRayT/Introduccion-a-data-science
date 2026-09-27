"""
Carga de datos limpios (CSV en /data/clean) hacia MySQL.

Requiere que:
  1. schema.sql ya se haya ejecutado sobre la base 'world_cup'
  2. clean_data.py ya se haya ejecutado (genera /data/clean/*.csv)

Ejecutar: python scripts/load_data.py
"""
import os
import math
import pandas as pd
from db_config import get_connection

CLEAN_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "clean")

# Orden de carga: respeta las dependencias de clave foránea definidas en schema.sql
LOAD_ORDER = [
    ("confederation.csv", "confederation",
     ["confederation_id", "confederation_name", "confederation_code", "confederation_wiki"]),
    ("federation.csv", "federation",
     ["federation_id", "federation_name", "federation_wiki", "confederation_id"]),
    ("region.csv", "region",
     ["region_id", "region_name"]),
    ("country.csv", "country",
     ["country_id", "country_name"]),
    ("city.csv", "city",
     ["city_id", "city_name", "country_id", "city_wiki"]),
    ("stadium.csv", "stadium",
     ["stadium_id", "stadium_name", "city_id", "stadium_capacity", "stadium_wiki"]),
    ("position.csv", "player_position",
     ["position_id", "position_name", "position_code"]),
    ("team.csv", "team",
     ["team_id", "team_name", "team_code", "mens_team", "womens_team",
      "federation_id", "region_id", "confederation_id",
      "mens_team_wiki", "womens_team_wiki"]),
    ("tournament.csv", "tournament",
     ["tournament_id", "tournament_name", "year", "start_date", "end_date",
      "host_country", "winner_team_id", "host_won", "count_teams",
      "group_stage", "second_group_stage", "final_round", "round_of_16",
      "quarter_finals", "semi_finals", "third_place_match", "final"]),
    ("matches.csv", "matches",
     ["match_id", "tournament_id", "match_name", "stage_name", "group_name",
      "group_stage", "knockout_stage", "replayed", "replay", "match_date",
      "match_time", "stadium_id", "home_team_id", "away_team_id",
      "home_team_score", "away_team_score", "home_team_score_margin",
      "away_team_score_margin", "extra_time", "penalty_shootout",
      "home_team_score_penalties", "away_team_score_penalties",
      "result", "home_team_win", "away_team_win", "draw"]),
    ("player.csv", "player",
     ["player_id", "family_name", "given_name", "birth_date", "female",
      "goal_keeper", "defender", "midfielder", "forward",
      "count_tournaments", "list_tournaments", "player_wiki"]),
    ("player_appearance.csv", "player_appearance",
     ["match_id", "team_id", "player_id", "position_id",
      "shirt_number", "starter", "substitute"]),
    ("goal.csv", "goal",
     ["goal_id", "match_id", "team_id", "player_id", "player_team_id",
      "shirt_number", "minute_label", "minute_regulation",
      "minute_stoppage", "match_period", "own_goal", "penalty"]),
    ("award.csv", "award",
     ["award_id", "award_name", "award_description", "year_introduced"]),
    ("award_winner.csv", "award_winner",
     ["tournament_id", "award_id", "shared", "player_id", "team_id"]),
]

BATCH_SIZE = 1000


def clean_value(v):
    """NaN/NaT de pandas -> None para que MySQL inserte NULL correctamente."""
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if pd.isna(v):
        return None
    return v


def load_table(cursor, csv_name, table_name, columns):
    path = os.path.join(CLEAN_DIR, csv_name)
    df = pd.read_csv(path)
    df = df[columns]  # asegura orden de columnas

    placeholders = ", ".join(["%s"] * len(columns))
    col_list = ", ".join(columns)
    insert_sql = f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})"

    rows = [tuple(clean_value(v) for v in row) for row in df.itertuples(index=False)]

    try:
        for i in range(0, len(rows), BATCH_SIZE):
            cursor.executemany(insert_sql, rows[i:i + BATCH_SIZE])
        print(f"[OK] {table_name}: {len(rows)} filas insertadas correctamente.")
    except Exception as e:
        print(f"[ERROR] {table_name}: falló la carga -> {e}")
        raise


def main():
    conn = get_connection()
    cursor = conn.cursor()
    print("=== Iniciando carga hacia MySQL (world_cup) ===\n")

    try:
        for csv_name, table_name, columns in LOAD_ORDER:
            load_table(cursor, csv_name, table_name, columns)
        conn.commit()
        print("\n=== Carga completa. Cambios confirmados (commit). ===")
    except Exception:
        conn.rollback()
        print("\n=== Ocurrió un error. Se revirtieron los cambios (rollback). ===")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
