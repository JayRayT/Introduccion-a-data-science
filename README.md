
# World Cup Database — Avance 1



## Descripción del proyecto
Base de datos relacional que almacena datos históricos de los Mundiales de la
FIFA (torneos, partidos, equipos, jugadores, goles, apariciones y premios),
junto con un conjunto de scripts en Python que limpian los CSV originales y
los cargan a MySQL.

Los datos fuente vienen parcialmente desnormalizados: catálogos como
`country`, `city`, `region`, `federation` y `position` no existen como
archivo propio, sino como columnas repetidas dentro de `teams.csv`,
`stadiums.csv` y `player_appearances.csv`. El script `clean_data.py` extrae
y deduplica esos catálogos antes de cargarlos.

## Tecnologías utilizadas
- Python 3.10+
- pandas (lectura y transformación de CSV)
- MySQL 8.0
- mysql-connector-python (conexión e inserción)
- python-dotenv (manejo de credenciales)

## Estructura del repositorio
```
worldcup_db/
├── data/                  # CSV originales (y /clean generado por el script)
├── sql/
│   └── schema.sql         # DDL: 15 tablas, PKs, FKs
├── scripts/
│   ├── db_config.py       # Conexión a MySQL vía variables de entorno
│   ├── clean_data.py      # Limpieza + extracción de catálogos
│   ├── load_data.py       # Carga de CSV limpios a MySQL
│   ├── validate_load.py   # Verificación de integridad post-carga
│   └── main.py            # Orquesta limpieza + carga en un solo paso
├── requirements.txt
├── .env.example
└── README.md
```

## Modelo de datos
14 entidades pedidas en el enunciado, resueltas en 15 tablas (award y
award_winner son dos tablas separadas dentro de ese conjunto de 14):

`confederation → federation → region → country → city → stadium`
`→ team → tournament → matches → player → player_appearance / goal`
`→ player_position, award → award_winner`

Decisiones de diseño relevantes:
- **city / country**: se derivan únicamente de `stadiums.csv`, ya que
  `matches.csv` referencia el mismo `stadium_id` y no aporta países/ciudades
  adicionales (verificado: mismos 20 países en ambos archivos).
- **tournament.host_country**: se guarda como texto (no FK) porque algunos
  torneos históricos tienen anfitriones que no coinciden 1:1 con el catálogo
  de países actual (ej. "West Germany", o co-anfitriones como "Korea, Japan"
  en 2002).
- **tournament.winner_team_id**: sí es FK a `team`, porque los 30 valores de
  `winner` en `tournaments.csv` coinciden exactamente con `team_name`.
- **goal.team_id vs goal.player_team_id**: se mantienen ambos porque difieren
  en autogoles (79 casos en los datos).
- **player_position (no `position`)**: la tabla se llama `player_position` y
  no `position` porque `POSITION` es palabra reservada en MySQL 8.0.13+
  (choca con la función `POSITION()`), lo que rompe la sintaxis al usarla en
  una cláusula `REFERENCES`.

## Instrucciones para ejecutar la base de datos

1. Instalar MySQL 8.0 y tener el servidor corriendo.
2. Ejecutar el script de esquema:
   ```bash
   mysql -u root -p < sql/schema.sql
   ```
   Esto crea la base `world_cup` con las 15 tablas, sus llaves primarias,
   foráneas y restricciones de integridad referencial.

## Instrucciones para ejecutar los scripts de carga

1. Crear entorno virtual e instalar dependencias:
   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Copiar `.env.example` a `.env` y completar las credenciales de MySQL:
   ```bash
   cp .env.example .env
   ```
3. Correr el proceso completo (limpieza + carga) desde la carpeta `scripts/`:
   ```bash
   cd scripts
   python main.py
   ```
   O por separado:
   ```bash
   python clean_data.py     # genera data/clean/*.csv
   python load_data.py      # inserta en MySQL
   ```
4. (Opcional) Validar integridad referencial post-carga:
   ```bash
   python validate_load.py
   ```

Cada paso imprime en consola cuántas filas se procesaron/insertaron por
tabla, y hace `rollback` automático si alguna carga falla a mitad de camino.

# Introduccion-a-data-science
>>>>>>> 2d83e585c3120d2c3064bb2dd9b4601cfd96c22d
