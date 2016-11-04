-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--


-- For debugging and testing.
-- DROP DATABASE tournament;

CREATE DATABASE tournament;
\c tournament

-- For generating tournament numbers.
CREATE SEQUENCE serial START 0 MINVALUE 0;

CREATE TABLE allstandings (
    -- tournament_id SERIAL PRIMARY KEY,
    tournament_id INTEGER,
    player_id INTEGER,
    wins INTEGER,
    losses INTEGER,
    ties INTEGER,
    byes INTEGER,
    score INTEGER,
    matches INTEGER,
    PRIMARY KEY (tournament_id,player_id)
);

CREATE TABLE allplayers (
    -- id SERIAL PRIMARY KEY,
    tournament_id INTEGER,
    player_id INTEGER,
    name TEXT,
    PRIMARY KEY (tournament_id,player_id)
);

CREATE TABLE allmatches (
    tournament_id INTEGER,
    match_id INTEGER,
    winner_id INTEGER,
    loser_id INTEGER,
    tie BOOLEAN,
    round_num INTEGER,
    PRIMARY KEY (tournament_id,match_id)
);

-- CREATE VIEW course_size AS
-- SELECT course_id, count(*) AS num FROM enrollment
-- GROUP BY course_id;

