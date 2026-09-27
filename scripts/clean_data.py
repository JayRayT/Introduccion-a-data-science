"""
Limpieza y extracción de catálogos.

Varios CSV originales vienen desnormalizados: 'country', 'city', 'region',
'federation' y 'position' no existen como archivo propio, sino como columnas
repetidas dentro de teams.csv, stadiums.csv y player_appearances.csv.

Este script:
  1. Lee los CSV crudos desde /data
  2. Extrae y deduplica los catálogos faltantes, generando IDs propios
  3. Limpia tipos de datos (fechas, booleanos, nulos)
  4. Guarda todo en /data/clean como CSV listos para cargar a MySQL

Ejecutar antes que load_data.py
"""
import os
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CLEAN_DIR = os.path.join(RAW_DIR, "clean")
os.makedirs(CLEAN_DIR, exist_ok=True)


def to_bool(series):
    """Convierte columnas 0/1 a booleano real, tolerando NaN."""
    return series.fillna(0).astype(int).astype(bool)


def read_raw(name):
    return pd.read_csv(os.path.join(RAW_DIR, name))


def save_clean(df, name):
    path = os.path.join(CLEAN_DIR, name)
    df.to_csv(path, index=False)
    print(f"[clean] {name}: {len(df)} filas -> {path}")


def build_confederation():
    df = read_raw("confederations.csv")
    out = df.rename(columns={
        "confederation_wikipedia_link": "confederation_wiki"
    })[["confederation_id", "confederation_name", "confederation_code", "confederation_wiki"]]
    out = out.drop_duplicates(subset=["confederation_id"])
    save_clean(out, "confederation.csv")
    return out


def build_federation(teams_raw):
    cat = teams_raw[["federation_name", "confederation_id", "federation_wikipedia_link"]] \
        .drop_duplicates(subset=["federation_name"]) \
        .reset_index(drop=True)
    cat["federation_id"] = ["FED-" + str(i + 1).zfill(3) for i in cat.index]
    cat = cat.rename(columns={"federation_wikipedia_link": "federation_wiki"})
    out = cat[["federation_id", "federation_name", "federation_wiki", "confederation_id"]]
    save_clean(out, "federation.csv")
    # mapa nombre -> id, para usar al construir team.csv
    return out, dict(zip(cat["federation_name"], cat["federation_id"]))


def build_region(teams_raw):
    cat = teams_raw[["region_name"]].drop_duplicates().reset_index(drop=True)
    cat["region_id"] = ["REG-" + str(i + 1).zfill(2) for i in cat.index]
    out = cat[["region_id", "region_name"]]
    save_clean(out, "region.csv")
    return out, dict(zip(cat["region_name"], cat["region_id"]))


def build_country(stadiums_raw):
    cat = stadiums_raw[["country_name"]].drop_duplicates().reset_index(drop=True)
    cat["country_id"] = ["C-" + str(i + 1).zfill(3) for i in cat.index]
    out = cat[["country_id", "country_name"]]
    save_clean(out, "country.csv")
    return out, dict(zip(cat["country_name"], cat["country_id"]))


def build_city(stadiums_raw, country_map):
    cat = stadiums_raw[["city_name", "country_name", "city_wikipedia_link"]] \
        .drop_duplicates(subset=["city_name", "country_name"]) \
        .reset_index(drop=True)
    cat["city_id"] = ["CTY-" + str(i + 1).zfill(3) for i in cat.index]
    cat["country_id"] = cat["country_name"].map(country_map)
    out = cat.rename(columns={"city_wikipedia_link": "city_wiki"})[
        ["city_id", "city_name", "country_id", "city_wiki"]
    ]
    save_clean(out, "city.csv")
    # mapa (city_name, country_name) -> city_id, para stadium.csv
    key_map = {(r.city_name, r.country_name): r.city_id for r in cat.itertuples()}
    return out, key_map


def build_stadium(stadiums_raw, city_key_map):
    df = stadiums_raw.copy()
    df["city_id"] = df.apply(
        lambda r: city_key_map[(r["city_name"], r["country_name"])], axis=1
    )
    out = df.rename(columns={
        "stadium_wikipedia_link": "stadium_wiki"
    })[["stadium_id", "stadium_name", "city_id", "stadium_capacity", "stadium_wiki"]]
    out = out.drop_duplicates(subset=["stadium_id"])
    save_clean(out, "stadium.csv")
    return out


def build_position(pa_raw):
    cat = pa_raw[["position_name", "position_code"]].drop_duplicates().reset_index(drop=True)
    cat["position_id"] = ["POS-" + str(i + 1).zfill(2) for i in cat.index]
    out = cat[["position_id", "position_name", "position_code"]]
    save_clean(out, "position.csv")
    return out, dict(zip(cat["position_code"], cat["position_id"]))


def build_team(teams_raw, federation_map, region_map):
    df = teams_raw.copy()
    df["federation_id"] = df["federation_name"].map(federation_map)
    df["region_id"] = df["region_name"].map(region_map)
    df["mens_team"] = to_bool(df["mens_team"])
    df["womens_team"] = to_bool(df["womens_team"])
    out = df.rename(columns={
        "mens_team_wikipedia_link": "mens_team_wiki",
        "womens_team_wikipedia_link": "womens_team_wiki",
    })[[
        "team_id", "team_name", "team_code", "mens_team", "womens_team",
        "federation_id", "region_id", "confederation_id",
        "mens_team_wiki", "womens_team_wiki",
    ]]
    out = out.drop_duplicates(subset=["team_id"])
    save_clean(out, "team.csv")
    return out


def build_tournament(tournaments_raw, team_name_to_id):
    df = tournaments_raw.copy()
    df["winner_team_id"] = df["winner"].map(team_name_to_id)
    bool_cols = ["host_won", "group_stage", "second_group_stage", "final_round",
                 "round_of_16", "quarter_finals", "semi_finals",
                 "third_place_match", "final"]
    for c in bool_cols:
        df[c] = to_bool(df[c])
    df["start_date"] = pd.to_datetime(df["start_date"]).dt.date
    df["end_date"] = pd.to_datetime(df["end_date"]).dt.date
    out = df[[
        "tournament_id", "tournament_name", "year", "start_date", "end_date",
        "host_country", "winner_team_id", "host_won", "count_teams",
        "group_stage", "second_group_stage", "final_round", "round_of_16",
        "quarter_finals", "semi_finals", "third_place_match", "final",
    ]]
    save_clean(out, "tournament.csv")
    return out


def build_matches(matches_raw):
    df = matches_raw.copy()
    bool_cols = ["group_stage", "knockout_stage", "replayed", "replay",
                 "extra_time", "penalty_shootout", "home_team_win",
                 "away_team_win", "draw"]
    for c in bool_cols:
        df[c] = to_bool(df[c])
    df["match_date"] = pd.to_datetime(df["match_date"]).dt.date
    out = df.rename(columns={"score_penalties": "score_penalties_str"})[[
        "match_id", "tournament_id", "match_name", "stage_name", "group_name",
        "group_stage", "knockout_stage", "replayed", "replay", "match_date",
        "match_time", "stadium_id", "home_team_id", "away_team_id",
        "home_team_score", "away_team_score", "home_team_score_margin",
        "away_team_score_margin", "extra_time", "penalty_shootout",
        "home_team_score_penalties", "away_team_score_penalties",
        "result", "home_team_win", "away_team_win", "draw",
    ]]
    out = out.drop_duplicates(subset=["match_id"])
    save_clean(out, "matches.csv")
    return out


def build_player(players_raw):
    df = players_raw.copy()
    bool_cols = ["female", "goal_keeper", "defender", "midfielder", "forward"]
    for c in bool_cols:
        df[c] = to_bool(df[c])
    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce").dt.date
    out = df.rename(columns={
        "player_wikipedia_link": "player_wiki"
    })[[
        "player_id", "family_name", "given_name", "birth_date", "female",
        "goal_keeper", "defender", "midfielder", "forward",
        "count_tournaments", "list_tournaments", "player_wiki",
    ]]
    out = out.drop_duplicates(subset=["player_id"])
    save_clean(out, "player.csv")
    return out


def build_player_appearance(pa_raw, position_map):
    df = pa_raw.copy()
    df["position_id"] = df["position_code"].map(position_map)
    df["starter"] = to_bool(df["starter"])
    df["substitute"] = to_bool(df["substitute"])
    out = df[["match_id", "team_id", "player_id", "position_id",
              "shirt_number", "starter", "substitute"]]
    out = out.drop_duplicates(subset=["match_id", "player_id"])
    save_clean(out, "player_appearance.csv")
    return out


def build_goal(goals_raw):
    df = goals_raw.copy()
    df["own_goal"] = to_bool(df["own_goal"])
    df["penalty"] = to_bool(df["penalty"])
    out = df[["goal_id", "match_id", "team_id", "player_id", "player_team_id",
              "shirt_number", "minute_label", "minute_regulation",
              "minute_stoppage", "match_period", "own_goal", "penalty"]]
    out = out.drop_duplicates(subset=["goal_id"])
    save_clean(out, "goal.csv")
    return out


def build_award(awards_raw):
    out = awards_raw[["award_id", "award_name", "award_description", "year_introduced"]]
    out = out.drop_duplicates(subset=["award_id"])
    save_clean(out, "award.csv")
    return out


def build_award_winner(aw_raw):
    df = aw_raw.copy()
    df["shared"] = to_bool(df["shared"])
    out = df[["tournament_id", "award_id", "shared", "player_id", "team_id"]]
    save_clean(out, "award_winner.csv")
    return out


def main():
    print("=== Iniciando limpieza y extracción de catálogos ===\n")

    teams_raw = read_raw("teams.csv")
    stadiums_raw = read_raw("stadiums.csv")

    build_confederation()
    federation_df, federation_map = build_federation(teams_raw)
    region_df, region_map = build_region(teams_raw)
    country_df, country_map = build_country(stadiums_raw)
    city_df, city_key_map = build_city(stadiums_raw, country_map)
    build_stadium(stadiums_raw, city_key_map)

    pa_raw = read_raw("player_appearances.csv")
    position_df, position_map = build_position(pa_raw)

    team_df = build_team(teams_raw, federation_map, region_map)
    team_name_to_id = dict(zip(team_df["team_name"], team_df["team_id"]))

    build_tournament(read_raw("tournaments.csv"), team_name_to_id)
    build_matches(read_raw("matches.csv"))
    build_player(read_raw("players.csv"))
    build_player_appearance(pa_raw, position_map)
    build_goal(read_raw("goals.csv"))
    build_award(read_raw("awards.csv"))
    build_award_winner(read_raw("award_winners.csv"))

    print("\n=== Limpieza completa. Archivos listos en /data/clean ===")


if __name__ == "__main__":
    main()
