"""
Validación post-carga: cuenta filas por tabla y busca claves foráneas
huérfanas directamente en MySQL. Útil para confirmar integridad referencial.

Uso:
    python scripts/validate_load.py
"""
from db_config import get_connection

TABLES = [
    "confederation", "federation", "region", "country", "city", "stadium",
    "player_position", "team", "tournament", "matches", "player",
    "player_appearance", "goal", "award", "award_winner",
]

ORPHAN_CHECKS = {
    "matches -> tournament": """
        SELECT COUNT(*) FROM matches m
        LEFT JOIN tournament t ON m.tournament_id = t.tournament_id
        WHERE t.tournament_id IS NULL""",
    "matches -> team (home)": """
        SELECT COUNT(*) FROM matches m
        LEFT JOIN team t ON m.home_team_id = t.team_id
        WHERE t.team_id IS NULL""",
    "player_appearance -> player": """
        SELECT COUNT(*) FROM player_appearance pa
        LEFT JOIN player p ON pa.player_id = p.player_id
        WHERE p.player_id IS NULL""",
    "goal -> match": """
        SELECT COUNT(*) FROM goal g
        LEFT JOIN matches m ON g.match_id = m.match_id
        WHERE m.match_id IS NULL""",
    "award_winner -> award": """
        SELECT COUNT(*) FROM award_winner aw
        LEFT JOIN award a ON aw.award_id = a.award_id
        WHERE a.award_id IS NULL""",
}


def main():
    conn = get_connection()
    cursor = conn.cursor()

    print("=== Conteo de filas por tabla ===")
    for table in TABLES:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count}")

    print("\n=== Búsqueda de claves foráneas huérfanas ===")
    all_ok = True
    for name, query in ORPHAN_CHECKS.items():
        cursor.execute(query)
        orphans = cursor.fetchone()[0]
        status = "OK" if orphans == 0 else f"⚠ {orphans} huérfanos"
        if orphans != 0:
            all_ok = False
        print(f"  {name}: {status}")

    print("\n=== Resultado:", "TODO OK" if all_ok else "REVISAR ERRORES ARRIBA", "===")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
