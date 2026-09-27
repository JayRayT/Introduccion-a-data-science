"""
Configuración de conexión a MySQL.
Lee credenciales desde variables de entorno (.env) para no hardcodearlas.
"""
import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "world_cup"),
}


def get_connection():
    """Crea y retorna una nueva conexión a MySQL."""
    return mysql.connector.connect(**DB_CONFIG)
