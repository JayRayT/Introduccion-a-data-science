-- =====================================================================
-- Base de datos: FIFA World Cup - Datos Históricos
-- Avance 1 - Modelo relacional
-- =====================================================================
-- Orden de creación respeta las dependencias de claves foráneas:
-- confederation -> federation -> region -> country -> city -> stadium
-- confederation/federation/region -> team
-- tournament -> team (winner) -> matches -> player -> player_appearance/goal
-- player_position -> player_appearance
-- award -> award_winner
-- =====================================================================

CREATE DATABASE IF NOT EXISTS world_cup
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE world_cup;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS goal;
DROP TABLE IF EXISTS player_appearance;
DROP TABLE IF EXISTS award_winner;
DROP TABLE IF EXISTS matches;
DROP TABLE IF EXISTS player;
DROP TABLE IF EXISTS award;
DROP TABLE IF EXISTS player_position;
DROP TABLE IF EXISTS team;
DROP TABLE IF EXISTS tournament;
DROP TABLE IF EXISTS stadium;
DROP TABLE IF EXISTS city;
DROP TABLE IF EXISTS country;
DROP TABLE IF EXISTS region;
DROP TABLE IF EXISTS federation;
DROP TABLE IF EXISTS confederation;

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- 1. CONFEDERATION  (catálogo, viene directo de confederations.csv)
-- =====================================================================
CREATE TABLE confederation (
    confederation_id      VARCHAR(10)  PRIMARY KEY,
    confederation_name    VARCHAR(100) NOT NULL,
    confederation_code    VARCHAR(10)  NOT NULL,
    confederation_wiki    VARCHAR(255)
);

-- =====================================================================
-- 2. FEDERATION (derivada de teams.csv: federation_name + confederation_id)
-- =====================================================================
CREATE TABLE federation (
    federation_id          VARCHAR(10) PRIMARY KEY,
    federation_name        VARCHAR(150) NOT NULL,
    federation_wiki         VARCHAR(255),
    confederation_id       VARCHAR(10),
    CONSTRAINT fk_federation_confederation
        FOREIGN KEY (confederation_id) REFERENCES confederation(confederation_id)
);

-- =====================================================================
-- 3. REGION (derivada de teams.csv: region_name)
-- =====================================================================
CREATE TABLE region (
    region_id     VARCHAR(10) PRIMARY KEY,
    region_name   VARCHAR(100) NOT NULL UNIQUE
);

-- =====================================================================
-- 4. COUNTRY (derivada de stadiums.csv: country_name)
-- =====================================================================
CREATE TABLE country (
    country_id    VARCHAR(10) PRIMARY KEY,
    country_name  VARCHAR(100) NOT NULL UNIQUE
);

-- =====================================================================
-- 5. CITY (derivada de stadiums.csv: city_name + country_name,
--          incluye city_wikipedia_link)
-- =====================================================================
CREATE TABLE city (
    city_id       VARCHAR(10) PRIMARY KEY,
    city_name     VARCHAR(150) NOT NULL,
    country_id    VARCHAR(10) NOT NULL,
    city_wiki     VARCHAR(255),
    CONSTRAINT fk_city_country
        FOREIGN KEY (country_id) REFERENCES country(country_id)
);

-- =====================================================================
-- 6. STADIUM
-- =====================================================================
CREATE TABLE stadium (
    stadium_id        VARCHAR(10) PRIMARY KEY,
    stadium_name      VARCHAR(150) NOT NULL,
    city_id           VARCHAR(10) NOT NULL,
    stadium_capacity  INT,
    stadium_wiki      VARCHAR(255),
    CONSTRAINT fk_stadium_city
        FOREIGN KEY (city_id) REFERENCES city(city_id)
);

-- =====================================================================
-- 7. POSITION (derivada de player_appearances.csv)
-- =====================================================================
CREATE TABLE player_position (
    position_id      VARCHAR(10) PRIMARY KEY,
    position_name    VARCHAR(50) NOT NULL,
    position_code    VARCHAR(5)  NOT NULL UNIQUE
);

-- =====================================================================
-- 8. TEAM
-- =====================================================================
CREATE TABLE team (
    team_id          VARCHAR(10) PRIMARY KEY,
    team_name        VARCHAR(100) NOT NULL,
    team_code        VARCHAR(5)   NOT NULL,
    mens_team        BOOLEAN NOT NULL DEFAULT FALSE,
    womens_team      BOOLEAN NOT NULL DEFAULT FALSE,
    federation_id    VARCHAR(10),
    region_id        VARCHAR(10),
    confederation_id VARCHAR(10),
    mens_team_wiki   VARCHAR(255),
    womens_team_wiki VARCHAR(255),
    CONSTRAINT fk_team_federation
        FOREIGN KEY (federation_id) REFERENCES federation(federation_id),
    CONSTRAINT fk_team_region
        FOREIGN KEY (region_id) REFERENCES region(region_id),
    CONSTRAINT fk_team_confederation
        FOREIGN KEY (confederation_id) REFERENCES confederation(confederation_id)
);

-- =====================================================================
-- 9. TOURNAMENT
--    host_country se guarda como texto: algunos torneos históricos
--    tienen host_country ("West Germany", "Korea, Japan") que no
--    coincide 1:1 con el catálogo actual de country/team (co-anfitriones
--    o nombres de países que ya no existen), por lo que no se fuerza FK.
--    winner sí es un equipo válido en todos los casos -> FK a team.
-- =====================================================================
CREATE TABLE tournament (
    tournament_id        VARCHAR(15) PRIMARY KEY,
    tournament_name      VARCHAR(100) NOT NULL,
    year                 INT NOT NULL,
    start_date           DATE,
    end_date             DATE,
    host_country         VARCHAR(100),
    winner_team_id       VARCHAR(10),
    host_won             BOOLEAN,
    count_teams          INT,
    group_stage          BOOLEAN,
    second_group_stage   BOOLEAN,
    final_round          BOOLEAN,
    round_of_16          BOOLEAN,
    quarter_finals       BOOLEAN,
    semi_finals          BOOLEAN,
    third_place_match    BOOLEAN,
    final                BOOLEAN,
    CONSTRAINT fk_tournament_winner
        FOREIGN KEY (winner_team_id) REFERENCES team(team_id)
);

-- =====================================================================
-- 10. MATCHES
--     city_name/country_name/stadium_name del CSV original son
--     redundantes con stadium_id (ya trae esa info) -> no se repiten.
-- =====================================================================
CREATE TABLE matches (
    match_id                  VARCHAR(15) PRIMARY KEY,
    tournament_id             VARCHAR(15) NOT NULL,
    match_name                VARCHAR(150),
    stage_name                VARCHAR(50),
    group_name                VARCHAR(50),
    group_stage               BOOLEAN,
    knockout_stage             BOOLEAN,
    replayed                  BOOLEAN,
    replay                    BOOLEAN,
    match_date                DATE,
    match_time                TIME,
    stadium_id                VARCHAR(10),
    home_team_id              VARCHAR(10),
    away_team_id              VARCHAR(10),
    home_team_score           INT,
    away_team_score           INT,
    home_team_score_margin    INT,
    away_team_score_margin    INT,
    extra_time                BOOLEAN,
    penalty_shootout           BOOLEAN,
    home_team_score_penalties INT,
    away_team_score_penalties INT,
    result                    VARCHAR(30),
    home_team_win             BOOLEAN,
    away_team_win             BOOLEAN,
    draw                      BOOLEAN,
    CONSTRAINT fk_matches_tournament
        FOREIGN KEY (tournament_id) REFERENCES tournament(tournament_id),
    CONSTRAINT fk_matches_stadium
        FOREIGN KEY (stadium_id) REFERENCES stadium(stadium_id),
    CONSTRAINT fk_matches_home_team
        FOREIGN KEY (home_team_id) REFERENCES team(team_id),
    CONSTRAINT fk_matches_away_team
        FOREIGN KEY (away_team_id) REFERENCES team(team_id)
);

-- =====================================================================
-- 11. PLAYER
-- =====================================================================
CREATE TABLE player (
    player_id          VARCHAR(10) PRIMARY KEY,
    family_name        VARCHAR(100),
    given_name         VARCHAR(100),
    birth_date         DATE,
    female             BOOLEAN,
    goal_keeper        BOOLEAN,
    defender           BOOLEAN,
    midfielder         BOOLEAN,
    forward            BOOLEAN,
    count_tournaments  INT,
    list_tournaments   VARCHAR(100),
    player_wiki        VARCHAR(255)
);

-- =====================================================================
-- 12. PLAYER_APPEARANCE
-- =====================================================================
CREATE TABLE player_appearance (
    appearance_id  INT AUTO_INCREMENT PRIMARY KEY,
    match_id       VARCHAR(15) NOT NULL,
    team_id        VARCHAR(10) NOT NULL,
    player_id      VARCHAR(10) NOT NULL,
    position_id    VARCHAR(10),
    shirt_number   INT,
    starter        BOOLEAN,
    substitute     BOOLEAN,
    CONSTRAINT fk_appearance_match
        FOREIGN KEY (match_id) REFERENCES matches(match_id),
    CONSTRAINT fk_appearance_team
        FOREIGN KEY (team_id) REFERENCES team(team_id),
    CONSTRAINT fk_appearance_player
        FOREIGN KEY (player_id) REFERENCES player(player_id),
    CONSTRAINT fk_appearance_position
        FOREIGN KEY (position_id) REFERENCES player_position(position_id),
    CONSTRAINT uq_appearance UNIQUE (match_id, player_id)
);

-- =====================================================================
-- 13. GOAL
--     team_id = equipo al que se le anota el gol (a favor de)
--     player_team_id = equipo del jugador que convierte el gol
--     (difieren en autogoles)
-- =====================================================================
CREATE TABLE goal (
    goal_id             VARCHAR(10) PRIMARY KEY,
    match_id            VARCHAR(15) NOT NULL,
    team_id             VARCHAR(10) NOT NULL,
    player_id           VARCHAR(10) NOT NULL,
    player_team_id      VARCHAR(10),
    shirt_number        INT,
    minute_label        VARCHAR(10),
    minute_regulation   INT,
    minute_stoppage     INT,
    match_period        VARCHAR(30),
    own_goal            BOOLEAN,
    penalty             BOOLEAN,
    CONSTRAINT fk_goal_match
        FOREIGN KEY (match_id) REFERENCES matches(match_id),
    CONSTRAINT fk_goal_team
        FOREIGN KEY (team_id) REFERENCES team(team_id),
    CONSTRAINT fk_goal_player
        FOREIGN KEY (player_id) REFERENCES player(player_id),
    CONSTRAINT fk_goal_player_team
        FOREIGN KEY (player_team_id) REFERENCES team(team_id)
);

-- =====================================================================
-- 14. AWARD
-- =====================================================================
CREATE TABLE award (
    award_id           VARCHAR(10) PRIMARY KEY,
    award_name         VARCHAR(100) NOT NULL,
    award_description  VARCHAR(255),
    year_introduced    INT
);

-- =====================================================================
-- 15. AWARD_WINNER
--     (nota: el enunciado pide 14 tablas; award/award_winner cuentan
--      como 2 de ellas, ver README para el detalle 1 a 1 con la rúbrica)
-- =====================================================================
CREATE TABLE award_winner (
    award_winner_id  INT AUTO_INCREMENT PRIMARY KEY,
    tournament_id    VARCHAR(15) NOT NULL,
    award_id         VARCHAR(10) NOT NULL,
    shared           BOOLEAN,
    player_id        VARCHAR(10),
    team_id          VARCHAR(10),
    CONSTRAINT fk_awardwinner_tournament
        FOREIGN KEY (tournament_id) REFERENCES tournament(tournament_id),
    CONSTRAINT fk_awardwinner_award
        FOREIGN KEY (award_id) REFERENCES award(award_id),
    CONSTRAINT fk_awardwinner_player
        FOREIGN KEY (player_id) REFERENCES player(player_id),
    CONSTRAINT fk_awardwinner_team
        FOREIGN KEY (team_id) REFERENCES team(team_id)
);
