
"""Run dummy tournaments for testing purposes."""

from tournament.tournament import *

######## Tournament 1 ########
## This is an example of a tournament with an odd number of players.
test_1_players = ["Twilight Sparkle",
                  "Fluttershy",
                  "Applejack",
                  "Pinkie Pie",
                  "Rarity",
                  "Rainbow Dash",
                  "Princess Celestia",
                  "Princess Luna",
                  "Willie",
                  "Joe",
                  "Ralph"]
simulateTournament(test_1_players)


######## Tournament 2 ########
## This is one example of a tournament with an odd number of players.
# test_2_players = ["Player 1",
                  # "Player 2",
                  # "Player 3",
                  # "Player 4"]
# simulateTournament(test_2_players)



# View players in the permanent table allplayers and standings in allstandings:
viewPermanentTables()
