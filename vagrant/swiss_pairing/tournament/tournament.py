#!/usr/bin/env python

""" Module functions:

connect - Get connection and cursor for the tournament database.
saveTournament - Save data from a completed tournament.
generateTables - Generate temporary tables for the current tournament.
deleteTables - Delete the temporary tables used for the current tournament.
deleteMatches - Remove all the match data from the current tournament.
deletePlayers - Remove all player data from the current tournament.
registerPlayer - Add a player to the current tournament.
reportMatch - Record the outcome of a single match between two players.
reportByeMatch - Record the outcome of a bye match.

countPlayers - Get the number of players in the current tournament.
getWinners - Get the players with the highest score.
playerStandings - Get current player standings, sorted by score.
playerScores - Get current player scores, sorted by score.
getPlayerIds - Get current player ids.
playerScoresDict - Get playerScores() in dictionary form.
allExistingPairs - Get all matches that have been used in the current
                    tournament.
swissPairings - Get pairings for the next round of the current tournament.
createPairs - Create pairings from a pre-sorted list of player ids.
splitByScore - Split players by score.
reorderWithinGroup - Shuffle players with the same score.
checkPairings - Determine if a potential pairing is valid.
pairDown - Find new pairings for the current round.

simulateTournament - Simulate a tournament. For testing purposes.
viewPermanentTables - View permanent tournament tables.
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


def saveTournament():
    """Save data from a completed tournament."""
    db, cursor = connect()

    # Get a new identifier for this tournament:
    cursor.execute("SELECT nextval('serial');")
    tournament_num = cursor.fetchone()

    # Record player info:
    insert_player_string = """
        INSERT INTO allplayers (tournament_id, player_id, name)
            VALUES (%s, %s, %s);
    """
    cursor.execute("SELECT id, name FROM player;")
    players = cursor.fetchall()
    for player in players:
        player_tup = tuple([tournament_num]) + player
        cursor.execute(insert_player_string, player_tup)


    # Record standing info:
    insert_standing_string = """
        INSERT INTO allstandings
            (tournament_id, player_id, wins, losses, ties, byes, score,
             matches)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """
    cursor.execute("SELECT * FROM standing;")
    records = cursor.fetchall()
    for record in records:
        # Don't need the unique id.
        standing_tup = tuple([tournament_num]) + record[1:]
        cursor.execute(insert_standing_string, standing_tup)


    # Record match info:
    insert_match_string = """
        INSERT INTO allmatches
            (tournament_id, match_id, winner_id, loser_id, tie, round_num)
            VALUES (%s, %s, %s, %s, %s, %s);
    """
    cursor.execute("SELECT * FROM match;")
    records = cursor.fetchall()
    for record in records:
        match_tup = tuple([tournament_num]) + record
        cursor.execute(insert_match_string, match_tup)

    db.commit()
    db.close()
    return None


def generateTables():
    """Generate temporary tables for the current tournament."""
    db, cursor = connect()

    cursor.execute("""
        CREATE TABLE player (
            id SERIAL PRIMARY KEY,
            name TEXT);
        """
    )

    # Could potentially remove the id column.
    cursor.execute("""
        CREATE TABLE standing (
            id SERIAL PRIMARY KEY,
            player_id INTEGER REFERENCES player (id),
            wins INTEGER,
            losses INTEGER,
            ties INTEGER,
            byes INTEGER,
            score INTEGER,
            matches INTEGER);
        """
    )

    cursor.execute("""
        CREATE TABLE match (
            id SERIAL PRIMARY KEY,
            winner_id INTEGER REFERENCES player (id),
            loser_id INTEGER REFERENCES player (id),
            tie BOOLEAN,
            round_num INTEGER);
        """
    )

    db.commit()
    db.close()
    return None


def deleteTables():
    """Delete the temporary tables used for the current tournament."""
    db, cursor = connect()

    cursor.execute("DROP TABLE match;")
    cursor.execute("DROP TABLE standing;")
    cursor.execute("DROP TABLE player;")

    db.commit()
    db.close()
    return None


def deleteMatches():
    """Remove all the match data from the current tournament."""
    db, cursor = connect()

    cursor.execute("DELETE FROM match;")
    cursor.execute("UPDATE standing SET wins = 0;")
    cursor.execute("UPDATE standing SET losses = 0;")
    cursor.execute("UPDATE standing SET ties = 0;")
    cursor.execute("UPDATE standing SET byes = 0;")
    cursor.execute("UPDATE standing SET score = 0;")
    cursor.execute("UPDATE standing SET matches = 0;")

    db.commit()
    db.close()
    return None


def deletePlayers():
    """Remove all player data from the current tournament."""
    db, cursor = connect()

    # Delete standing first because it references the player table.
    cursor.execute("DELETE FROM standing;")
    cursor.execute("DELETE FROM player;")

    db.commit()
    db.close()
    return None


def registerPlayer(name):
    """Add a player to the current tournament.

       Args:
        name: the player's full name (need not be unique).
    """
    db, cursor = connect()
    cursor.execute("INSERT INTO player (name) VALUES (%s) RETURNING id;",
                   (name,))
    new_player_id = int(cursor.fetchone()[0])

    insert_string = """
        INSERT INTO standing
            (player_id, wins, losses, ties, byes, score, matches)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    cursor.execute(insert_string, (new_player_id,0,0,0,0,0,0))

    db.commit()
    db.close()
    return None


def countPlayers():
    """Get the number of players in the current tournament."""
    db, cursor = connect()

    cursor.execute("SELECT COUNT(id) FROM player;")
    player_count = cursor.fetchone()[0]

    db.close()
    return player_count


def getWinners():
    """Get the players with the highest score."""
    db, cursor = connect()

    cursor.execute("""
        SELECT s.player_id, p.name, s.score FROM player p, standing s  
            WHERE p.id = s.player_id AND s.score = 
            (SELECT MAX(score) FROM standing);
        """
    )
    winners = cursor.fetchall()

    db.close()
    return winners


def playerStandings():
    """Get current player standings, sorted by score."""
    db, cursor = connect()
    
    cursor.execute("""
        SELECT player_id, name, wins, matches
            FROM standing, player WHERE standing.player_id = player.id
            ORDER BY score DESC;
        """
    )
    standings = cursor.fetchall()
    standings = [tuple(record) for record in standings]

    db.close()
    return standings


def playerScores():
    """Get current player scores, sorted by score."""
    db, cursor = connect()

    cursor.execute("""
        SELECT player_id, name, score
            FROM standing, player WHERE standing.player_id = player.id
            ORDER BY score DESC;
        """
    )
    standings = cursor.fetchall()
    standings = [tuple(record) for record in standings]

    db.close()
    return standings


def getPlayerIds():
    """Get current player ids."""
    db, cursor = connect()

    cursor.execute("SELECT id FROM player;")
    records = cursor.fetchall()
    ids = [record[0] for record in records]

    db.commit()
    db.close()
    return ids


def playerScoresDict():
    """Get playerScores() in dictionary form."""
    players_list = playerScores()
    players_dict = {str(player[0]): player for player in players_list}
    return players_dict


def allExistingPairs():
    """Get all matches that have been used in the current tournament."""
    db, cursor = connect()

    cursor.execute("SELECT winner_id, loser_id FROM match;")
    records = cursor.fetchall()
    pairings = [tuple([record[0],record[1]]) for record in records]

    db.commit()
    db.close()
    return pairings


def reportMatch(winner, loser, round_num, tie=False):
    """Record the outcome of a single match between two players.

       Args:
        winner: id number of the player who won (if not a tie).
        loser: id number of the player who lost (if not a tie).
        round_num: current round number.
        tie: Boolean indicating if the match ended in a tie. If True, the
             order of the winner and loser arguments does not matter.
    """
    db, cursor = connect()

    # Update match table:
    insert_string = """
        INSERT INTO match (winner_id, loser_id, tie, round_num)
            VALUES (%s,%s,%s,%s);
    """
    cursor.execute(insert_string, (winner, loser, tie, round_num))

    # Update standing table:
    if tie:
        tie_string = """
            UPDATE standing SET ties = ties + 1,
                                score = score + 1,
                                matches = matches + 1
            WHERE id = (%s);
        """
        cursor.execute(tie_string, (winner, ))
        cursor.execute(tie_string, (loser, ))
    else:
        win_string = """
            UPDATE standing SET wins = wins + 1,
                                score = score + 2,
                                matches = matches + 1
            WHERE id = (%s);
        """
        loss_string = """
            UPDATE standing SET losses = losses + 1,
                                matches = matches + 1
            WHERE id = (%s);
        """
        cursor.execute(win_string, (winner, ))
        cursor.execute(loss_string, (loser, ))

    db.commit()
    db.close()
    return None


def reportByeMatch(player, round_num):
    """Record the outcome of a bye match."""
    db, cursor = connect()

    # Update match table:
    insert_string = """
        INSERT INTO match (winner_id, loser_id, tie, round_num)
            VALUES (%s,%s,%s,%s);
    """
    cursor.execute(insert_string, (player, None, None, round_num))

    # Update standing table:
    tie_string = """
        UPDATE standing SET ties = ties + 1,
                            score = score + 1,
                            matches = matches + 1
            WHERE id = (%s);
    """
    cursor.execute(tie_string, (player, ))

    db.commit()
    db.close()
    return None


def swissPairings(round_num, verbose=False):
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
        player_ids = getPlayerIds()
        if len(player_ids) % 2 == 1:
            player_ids.append(None)     # to get a bye

        random.shuffle(player_ids)
        pairings_dict = createPairs(player_ids)

    else:
        # Dictionary containing players split by number of wins.
        players_by_wins = splitByScore()

        # This represents an "ideal" ordering, ignoring rematches.
        # For players with the same score, shuffle amongst themselves.
        ordered_ids = reorderWithinGroup(players_by_wins)
        if len(ordered_ids) % 2 == 1:
            ordered_ids.append(None)    # to get a bye

        
        # Find pairings without rematches.
        final_pairings_list_id = pairDown(x=ordered_ids, n=0)
        pairings_dict = createPairs(final_pairings_list_id)
        
    if verbose:
        for pair in pairings_dict.values():
            print pair
        print "\n"

    # Remove the bye player, if there is one, and record their score:
    bye_player = pairings_dict.get("bye")
    if bye_player:
        reportByeMatch(player=bye_player[0][0], round_num=round_num)
        pairings_dict.pop("bye")

    # Convert the dictionary to a list without the bye player:
    pairings = [v for v in pairings_dict.values()]

    return pairings


def createPairs(ids_list):
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
    players_dict = playerScoresDict()

    pairings_dict = {}
    n = len(ids_list)
    for i in range(0,(n-1),2):
        id1 = ids_list[i]
        id2 = ids_list[i+1]
        player1 = players_dict.get(str(id1))
        player2 = players_dict.get(str(id2))

        if player1 is None:
            pairings_dict["bye"] = tuple([player2[0:2],"BYE"])
        elif player2 is None:
            pairings_dict["bye"] = tuple([player1[0:2],"BYE"])
        else:
            pairings_dict[str(i)] = tuple([player1[0:2], player2[0:2]])

    return pairings_dict


def splitByScore():
    """Split players by score.

       Returns a dictionary where the keys are the scores and the values
       are the players.
    """
    players = playerScores()
    
    group_by_wins = {}
    for i in range(0,len(players)):
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
    for i in range(0,len(pairings)/2):
        pairings_in_tuples.append(tuple([pairings[i],pairings[i+1]]))

    p1 = pairing[0][0]
    p2 = pairing[0][1]

    tup1 = tuple([p1,p2])
    tup2 = tuple([p2,p1])

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

    for i in range(1,len(x)):
        # If you're starting a new value, remove any existing pair
        # that has that value as the FIRST value.
        if n > 0 and pairings[len(pairings)-2] == x[0]:
            del pairings[len(pairings)-1]     # backtrack
            del pairings[len(pairings)-1]

        pair = [[x[0],x[i]]]
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

    # Generate the temporary player, match, standing tables:
    generateTables()

    try:
        # Register players in temporary player table:
        for player in use_players:
            registerPlayer(player)

        # Number of matches and pairings:
        eff_num_of_players = countPlayers()
        if eff_num_of_players % 2 == 1:
            eff_num_of_players = eff_num_of_players - 1

        num_of_rounds = int(ceil(log(eff_num_of_players, 2)))
        # Not including byes:
        num_of_matches = num_of_rounds * eff_num_of_players/2

        for round in range(1,num_of_rounds + 1):
            print "Round", round, "pairings:"
            pairings = swissPairings(round_num=round, verbose=True)

            # Play the round:
            for i in range(len(pairings)):
                id_1 = pairings[i][0][0]
                id_2 = pairings[i][1][0]

                score = random.randint(0,2)
                if score == 2:
                    # Player 1 won.
                    reportMatch(winner=id_1, loser=id_2, round_num=round)
                elif score == 1:
                    # Tie.
                    reportMatch(winner=id_1, loser=id_2, round_num=round,
                                tie=True)
                else:
                    # Player 2 won.
                    reportMatch(winner=id_2, loser=id_1, round_num=round)

        # Save completed tournament:
        saveTournament()

        # Display the winner(s):
        print "WINNER(S):"
        for winner in getWinners():
            print "    ", winner
        print "\n\n"
        
        # Delete the temporary tables:
        deleteTables()

    except Exception, e:
        # If something goes wrong, make sure the temporary tables
        # still get deleted:
        print e
        
        deleteTables()


def viewPermanentTables():
    """View permanent tournament tables."""
    db, cursor = connect()
    
    cursor.execute("""
            SELECT * FROM allplayers;
        """
    )
    print "Players:"
    players = cursor.fetchall()
    for player in players:
        print player

        
    cursor.execute("""
            SELECT * FROM allstandings;
        """
    )
    print "\nStandings:"
    standings = cursor.fetchall()
    for standing in standings:
        print standing

    db.close()
