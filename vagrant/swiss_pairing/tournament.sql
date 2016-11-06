-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--


DROP DATABASE IF EXISTS tournament;

CREATE DATABASE tournament;
\c tournament

-- For generating tournament numbers.
CREATE SEQUENCE serial START 1 MINVALUE 1;

CREATE TABLE players (
    tournament_id INTEGER,
    player_id SERIAL,
    name TEXT,
    PRIMARY KEY (tournament_id,player_id)
);

CREATE TABLE matches (
    tournament_id INTEGER,
    match_id SERIAL,
    winner_id INTEGER,
    loser_id INTEGER,
    tie BOOLEAN,
    round_num INTEGER,
    PRIMARY KEY (tournament_id,match_id),
    FOREIGN KEY (tournament_id,winner_id) REFERENCES
        players (tournament_id,player_id),
    FOREIGN KEY (tournament_id,loser_id) REFERENCES
        players (tournament_id,player_id)
);
