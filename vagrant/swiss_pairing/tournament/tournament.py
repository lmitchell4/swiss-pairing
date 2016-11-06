#!/usr/bin/env python

""" Module functions:

connect - Get connection and cursor for the tournament database.
getTournamentNum - Get a new tournament number.
deleteTables - Delete the temporary tables used for the current tournament.
deleteMatches - Remove all the match data from the current tournament.
deletePlayers - Remove all player data from the current tournament.
registerPlayer - Add a player to the current tournament.
countPlayers - Get the number of players in the current tournament.
getWinners - Get the players with the highest score.
playerStandings - Get current player standings, sorted by score.
playerScores - Get current player scores, sorted by score.
getPlayerIds - Get current player ids.
playerScoresDict - Get playerScores() in dictionary form.
allExistingPairs - Get all matches that have been used in the current
                    tournament.

reportMatch - Record the outcome of a single match between two players.
reportByeMatch - Record the outcome of a bye match.

swissPairings - Get pairings for the next round of the current tournament.
createPairs - Create pairings from a pre-sorted list of player ids.
splitByScore - Split players by score.
reorderWithinGroup - Shuffle players with the same score.
checkPairings - Determine if a potential pairing is valid.
pairDown - Find new pairings for the current round.

simulateTournament - Simulate a tournament. For testing purposes.
"""

import random
from math import log, ceil
from itertools import chain

import psycopg2


def connect(database_name="tournament"):
    """Get connection and cursor for the tournament database."""
    try:
        db = psycopg2.connect("dbname={}".format(database_name))
        cursor = db.cursor()
        return db, cursor
    except:
        print "Error connecting to database", database_name


def getTournamentNum():
    """Get a new tournament number."""
    db, cursor = connect()

    cursor.execute("SELECT NEXTVAL('SERIAL');")
    tournament_num = cursor.fetchone()[0]

    db.commit()
    db.close()
    return tournament_num


def deleteTables():
    """Delete the temporary tables used for the current tournament."""
    db, cursor = connect()

    cursor.execute("DROP TABLE matches;")
    cursor.execute("DROP TABLE players;")

    db.commit()
    db.close()
    return None


def deleteMatches(tournament_num):
    """Remove all the match data from the current tournament."""
    db, cursor = connect()

    delete_str = """
        DELETE FROM matches WHERE tournament_id = (%s);
    """
    cursor.execute(delete_str, (tournament_num, ))

    db.commit()
    db.close()
    return None


def deletePlayers(tournament_num):
    """Remove all player data from the current tournament."""
    db, cursor = connect()

    delete_str = """
        DELETE FROM players WHERE tournament_id = (%s);
    """
    cursor.execute(delete_str, (tournament_num, ))

    db.commit()
    db.close()
    return None


def registerPlayer(tournament_num, name):
    """Add a player to the current tournament.

       Args:
        name: the player's full name (need not be unique).
    """
    db, cursor = connect()

    select_str = """
        INSERT INTO players (tournament_id, name) VALUES (%s, %s)
            RETURNING player_id;
    """
    cursor.execute(select_str, (tournament_num, name))
    new_player_id = int(cursor.fetchone()[0])

    db.commit()
    db.close()
    return None


def countPlayers(tournament_num):
    """Get the number of players in the current tournament."""
    db, cursor = connect()

    select_str = """
        SELECT COUNT(player_id) FROM players WHERE tournament_id = %s;
    """
    cursor.execute(select_str, (tournament_num, ))
    player_count = cursor.fetchone()[0]

    db.close()
    return player_count


def getWinners(tournament_num):
    """Get the players with the highest score."""
    db, cursor = connect()

    # Note: the views don't get committed, so they normally won't exist,
    # but they might if you're debugging.
    select_str = """
        DROP VIEW IF EXISTS scores_v;
        DROP VIEW IF EXISTS players_v;
        DROP VIEW IF EXISTS wins_v;
        DROP VIEW IF EXISTS ties_v;

        -- PLAYERS
        CREATE VIEW players_v AS
            SELECT player_id, name FROM players WHERE tournament_id = (%s);

        -- WINS
        CREATE VIEW wins_v AS
            SELECT winner_id AS player_id, COUNT(*) AS wins
                FROM matches
                WHERE tournament_id = (%s) AND tie = FALSE GROUP BY winner_id;

        -- TIES
        CREATE VIEW ties_v AS
            SELECT player_id, COUNT(*) AS ties FROM
            ((SELECT winner_id AS player_id FROM matches
                WHERE tournament_id = (%s) AND tie = TRUE) AS a
                FULL OUTER JOIN
             (SELECT loser_id AS player_id FROM matches
                WHERE tournament_id = (%s) AND tie = TRUE) AS b
            USING (player_id)) as c GROUP BY player_id;

        -- SCORES
        CREATE VIEW scores_v AS
            SELECT player_id, name, wins*2 + ties*1 AS score FROM  (
                SELECT player_id, name, COALESCE(wins,0) AS wins,
                    COALESCE(ties,0) AS ties FROM wins_v w
                    FULL OUTER JOIN ties_v t USING (player_id)
                    RIGHT OUTER JOIN players_v p USING (player_id)
            ) AS a
            ORDER BY score DESC;

        SELECT * FROM scores_v
            WHERE score = (SELECT MAX(score) FROM scores_v);
    """
    cursor.execute(select_str, (tournament_num, tournament_num,
                                tournament_num, tournament_num))
    winners = cursor.fetchall()

    db.close()
    return winners


def playerStandings(tournament_num):
    """Get current player standings, sorted by wins (excluding ties).
       This function exists for tournament_test.py.
    """
    db, cursor = connect()

    select_str = """
        DROP VIEW IF EXISTS players_v;
        DROP VIEW IF EXISTS wins_v;
        DROP VIEW IF EXISTS matches_v;

        -- PLAYERS
        CREATE VIEW players_v AS
            SELECT player_id, name FROM players WHERE tournament_id = (%s);

        -- WINS
        CREATE VIEW wins_v AS
            SELECT winner_id AS player_id, COUNT(*) AS wins
                FROM matches
                WHERE tournament_id = (%s) AND tie = FALSE GROUP BY winner_id;

        -- MATCHES
        CREATE VIEW matches_v AS
            SELECT player_id, COUNT(*) AS matches FROM
            ((SELECT winner_id AS player_id FROM matches
                WHERE tournament_id = (%s)) AS a FULL OUTER JOIN
            (SELECT loser_id AS player_id FROM matches
                WHERE tournament_id = (%s)) AS b
            USING (player_id)) AS c GROUP BY player_id;

        SELECT player_id, name, COALESCE(wins,0) AS wins,
            COALESCE(matches,0) AS matches FROM wins_v w
            FULL OUTER JOIN matches_v m USING (player_id)
            RIGHT OUTER JOIN players_v p USING (player_id)
        ORDER BY wins DESC;
    """
    cursor.execute(select_str, (tournament_num, tournament_num,
                                tournament_num, tournament_num))
    standings = cursor.fetchall()
    standings = [tuple(record) for record in standings]

    db.close()
    return standings


def playerScores(tournament_num):
    """Get current player scores, sorted by score."""
    db, cursor = connect()

    select_str = """
        DROP VIEW IF EXISTS players_v;
        DROP VIEW IF EXISTS wins_v;
        DROP VIEW IF EXISTS ties_v;

        -- PLAYERS
        CREATE VIEW players_v AS
            SELECT player_id, name FROM players WHERE tournament_id = (%s);

        -- WINS
        CREATE VIEW wins_v AS
            SELECT winner_id AS player_id, COUNT(*) AS wins
                FROM matches
                WHERE tournament_id = (%s) AND tie = FALSE GROUP BY winner_id;

        -- TIES
        CREATE VIEW ties_v AS
            SELECT player_id, COUNT(*) AS ties FROM
            ((SELECT winner_id AS player_id FROM matches
                WHERE tournament_id = (%s) AND tie = TRUE) AS a
                FULL OUTER JOIN
             (SELECT loser_id AS player_id FROM matches
                WHERE tournament_id = (%s) AND tie = TRUE) AS b
            USING (player_id)) as c GROUP BY player_id;


        SELECT player_id, name, wins*2 + ties*1 AS score FROM  (
            SELECT player_id, name, COALESCE(wins,0) AS wins,
                COALESCE(ties,0) AS ties FROM wins_v w
                FULL OUTER JOIN ties_v t USING (player_id)
                RIGHT OUTER JOIN players_v p USING (player_id)
        ) AS a
        ORDER BY score DESC;
    """
    cursor.execute(select_str, (tournament_num, tournament_num,
                                tournament_num, tournament_num))
    standings = cursor.fetchall()
    standings = [tuple(record) for record in standings]

    db.close()
    return standings


def getPlayerIds(tournament_num):
    """Get current player ids."""
    db, cursor = connect()

    select_str = """
        SELECT player_id FROM players WHERE tournament_id = (%s);
    """
    cursor.execute(select_str, (tournament_num, ))
    records = cursor.fetchall()
    ids = [record[0] for record in records]

    db.commit()
    db.close()
    return ids


def playerScoresDict(tournament_num):
    """Get playerScores() in dictionary form."""
    players_list = playerScores(tournament_num)
    players_dict = {str(player[0]): player for player in players_list}
    return players_dict


def allExistingPairs():
    """Get all matches that have been used in the current tournament."""
    db, cursor = connect()

    cursor.execute("SELECT winner_id, loser_id FROM matches;")
    records = cursor.fetchall()
    pairings = [tuple([record[0], record[1]]) for record in records]

    db.commit()
    db.close()
    return pairings


def reportMatch(tournament_num, winner, loser, round_num, tie=False):
    """Record the outcome of a single match between two players.

       Args:
        tournament_num: tournament number.
        winner: id number of the player who won (if not a tie).
        loser: id number of the player who lost (if not a tie).
        round_num: current round number.
        tie: Boolean indicating if the match ended in a tie. If True, the
             order of the winner and loser arguments does not matter.
    """
    db, cursor = connect()

    # Update match table:
    insert_string = """
        INSERT INTO matches
            (tournament_id, winner_id, loser_id, tie, round_num)
            VALUES (%s,%s,%s,%s,%s);
    """
    cursor.execute(insert_string,
                   (tournament_num, winner, loser, tie, round_num))

    db.commit()
    db.close()
    return None


def reportByeMatch(tournament_num, player, round_num):
    """Record the outcome of a bye match."""
    db, cursor = connect()

    # Update match table:
    insert_string = """
        INSERT INTO matches
            (tournament_id, winner_id, loser_id, tie, round_num)
            VALUES (%s,%s,%s,%s,%s);
    """
    cursor.execute(insert_string,
                   (tournament_num, player, None, None, round_num))

    db.commit()
    db.close()
    return None


def swissPairings(tournament_num, round_num, verbose=False):
    """Get pairings for the next round of the current tournament.

       Round 1:
       1) random pairings.
       2) if num of players is odd, unpaired player gets a bye.

       Round 2+:
       1) sort everyone by score.
       2) for duplicates by score, randomly order them amongst themselves.
       3) check for rematches and multiple byes.
    """
    if round_num == 1:
        player_ids = getPlayerIds(tournament_num)
        if len(player_ids) % 2 == 1:
            player_ids.append(None)     # to get a bye

        random.shuffle(player_ids)
        pairings_dict = createPairs(tournament_num, player_ids)

    else:
        # Dictionary containing players split by number of wins.
        players_by_wins = splitByScore(tournament_num)

        # This represents an "ideal" ordering, ignoring rematches.
        # For players with the same score, shuffle amongst themselves.
        ordered_ids = reorderWithinGroup(players_by_wins)
        if len(ordered_ids) % 2 == 1:
            ordered_ids.append(None)    # to get a bye

        # Find pairings without rematches.
        final_pairings_list_id = pairDown(x=ordered_ids, n=0)
        pairings_dict = createPairs(tournament_num, final_pairings_list_id)

    if verbose:
        for pair in pairings_dict.values():
            print pair
        print "\n"

    # Remove the bye player, if there is one, and record their score:
    bye_player = pairings_dict.get("bye")
    if bye_player:
        reportByeMatch(tournament_num, player=bye_player[0][0],
                       round_num=round_num)
        pairings_dict.pop("bye")

    # Convert the dictionary to a list without the bye player:
    pairings = [v for v in pairings_dict.values()]

    return pairings


def createPairs(tournament_num, ids_list):
    """Create pairings from a pre-sorted list of player ids.

       Go down the list and create pairings from the first two elements,
       then the next two elements, etc.
       If either player id is None, then that pairing is a BYE.

       Args:
        ids_list: a list of player ids, sorted accordingly to get the
                  desired pairings. The list should contain a None if
                  there needs to be a bye pairing.

       Returns a dictionary containing each pairing as a tuple.
       Only the key value "BYE" really matters.
    """
    players_dict = playerScoresDict(tournament_num)

    pairings_dict = {}
    n = len(ids_list)
    for i in range(0, (n-1), 2):
        id1 = ids_list[i]
        id2 = ids_list[i+1]
        player1 = players_dict.get(str(id1))
        player2 = players_dict.get(str(id2))

        if player1 is None:
            pairings_dict["bye"] = tuple([player2[0:2], "BYE"])
        elif player2 is None:
            pairings_dict["bye"] = tuple([player1[0:2], "BYE"])
        else:
            pairings_dict[str(i)] = tuple([player1[0:2], player2[0:2]])

    return pairings_dict


def splitByScore(tournament_num):
    """Split players by score.

       Returns a dictionary where the keys are the scores and the values
       are the players.
    """
    players = playerScores(tournament_num)

    group_by_wins = {}
    for i in range(0, len(players)):
        score = players[i][2]
        if score in group_by_wins.keys():
            group_by_wins[score].append(players[i])
        else:
            group_by_wins[score] = [players[i]]

    return group_by_wins


def reorderWithinGroup(players_by_wins):
    """Shuffle players with the same score.

       Args:
        players_by_wins: a dictionary returned by splitByScore().

       Returns a list of the re-ordered player ids.
    """
    for score in players_by_wins.keys():
        random.shuffle(players_by_wins[score])

    # players_by_wins is a dictionary with scores as keys. When
    # converting to a list, need to make sure it is sorted by score,
    # from highest to lowest.
    players_ordered = []
    score_keys = players_by_wins.keys()
    score_keys.sort(reverse=True)
    for score in score_keys:
        players_ordered.append(players_by_wins[score])

    # Convert back to a list.
    players_ordered = list(chain.from_iterable(players_ordered))

    # Return the ordered ids.
    ordered_ids = [x[0] for x in players_ordered]

    return(ordered_ids)


def checkPairings(pairing, pairings, previous_pairings):
    """Determine if a potential pairing is valid.

       A pairing is valid if it has not already been used in the current
       tournament, and neither player id is in the current set of pairings
       currently being constructed.

       Args:
        pairing: a list containing a list containing two player ids.
        pairings: a list of player ids representing the current set of
                  pairings being constructed. The first two elements are
                  paired together, then the next two, etc.
        previous_pairings: a list containing tuple pairings that have
                           already been used in the current tournament.
    """
    pairings_in_tuples = []
    for i in range(0, len(pairings)/2):
        pairings_in_tuples.append(tuple([pairings[i], pairings[i+1]]))

    p1 = pairing[0][0]
    p2 = pairing[0][1]

    tup1 = tuple([p1, p2])
    tup2 = tuple([p2, p1])

    if tup1 in previous_pairings or tup2 in previous_pairings:
        return False
    elif p1 in pairings or p2 in pairings:
        return False
    else:
        return True


def pairDown(x, n=0, previous_pairings=None, N=None, pairings=None):
    """Find new pairings for the current round.

       Make sure there are no rematches.
       Make sure no player has more than one bye.
    """
    if n == 0:
        N = len(x)
        previous_pairings = allExistingPairs()
        pairings = []

    for i in range(1, len(x)):
        # If you're starting a new value, remove any existing pair
        # that has that value as the FIRST value.
        if n > 0 and pairings[len(pairings)-2] == x[0]:
            del pairings[len(pairings)-1]     # backtrack
            del pairings[len(pairings)-1]

        pair = [[x[0], x[i]]]
        if checkPairings(pair, pairings, previous_pairings):
            if len(pairings) == (N - 2):
                return pair
            else:
                y = [j for j in x]  # copy of x
                del y[i]
                del y[0]

                pairings.append(x[0])
                pairings.append(x[i])

                tmp = pairDown(y, n+1, previous_pairings, N, pairings)
                if tmp:
                    if len(pairings) < N:
                        for result in tmp:
                            pairings.append(result[0])
                            pairings.append(result[1])
                            return pairings

        if n == 0:
            if len(pairings) == N:
                return pairings
            else:
                pairings = []


def simulateTournament(use_players):
    """Simulate a tournament. For testing purposes."""
    print "Running Test Tournament .......\n"

    tournament_num = getTournamentNum()

    try:
        # Register players in temporary player table:
        for player in use_players:
            registerPlayer(tournament_num, player)

        # Number of matches and pairings:
        eff_num_of_players = countPlayers(tournament_num)
        if eff_num_of_players % 2 == 1:
            eff_num_of_players = eff_num_of_players - 1

        num_of_rounds = int(ceil(log(eff_num_of_players, 2)))
        # Not including byes:
        num_of_matches = num_of_rounds * eff_num_of_players/2

        for round in range(1, num_of_rounds + 1):
            print "Round", round, "pairings:"
            pairings = swissPairings(tournament_num, round_num=round,
                                     verbose=True)

            # Play the round:
            for i in range(len(pairings)):
                id_1 = pairings[i][0][0]
                id_2 = pairings[i][1][0]

                score = random.randint(0, 2)
                if score == 2:
                    # Player 1 won.
                    reportMatch(tournament_num=tournament_num,
                                winner=id_1, loser=id_2, round_num=round)
                elif score == 1:
                    # Tie.
                    reportMatch(tournament_num=tournament_num,
                                winner=id_1, loser=id_2, round_num=round,
                                tie=True)
                else:
                    # Player 2 won.
                    reportMatch(tournament_num=tournament_num,
                                winner=id_2, loser=id_1, round_num=round)

        # Display the winner(s):
        print "WINNER(S):"
        for winner in getWinners(tournament_num):
            print "    ", winner
        print "\n"

    except Exception, e:
        # If something goes wrong, make sure the temporary tables
        # still get deleted:
        print e
