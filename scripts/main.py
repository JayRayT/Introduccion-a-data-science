"""
Orquesta el proceso completo: limpieza de datos -> carga a MySQL.

Uso:
    python scripts/main.py
"""
import clean_data
import load_data

if __name__ == "__main__":
    print(">>> PASO 1/2: Limpieza y extracción de catálogos\n")
    clean_data.main()

    print("\n>>> PASO 2/2: Carga hacia MySQL\n")
    load_data.main()
