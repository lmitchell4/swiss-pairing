
# Swiss pairing tournament

This program allows you to organize and record tournaments based on the Swiss 
pairing system. 
It generates matches between players of relatively equal 
skill levels and prevents rematches. It saves data from 
completed tournaments in a PostgreSQL database.

### Installation

The Swiss pairing tournament program requires Python 2.7 and PostgreSQL.

You have two options for how to install and run the program. The first is to 
use your own Python and PostgreSQL installations. In this case, you can extract 
the directory swiss-pairing and use the code in there directly. The second option 
is to run the code on the Vagrant Virtual Machine provided in this repo, which 
has PostgreSQL installed, configured, and ready to go. The VM used here is 
based on the Vagrant VM provided in the 
[udacity/fullstack-nanodegree-vm](https://github.com/udacity/fullstack-nanodegree-vm) 
repo. 

If you've chosen option two, here are steps for getting the VM up and running:

1. Download and install [Git](https://git-scm.com/downloads)

2. Install [Vagrant]( https://www.vagrantup.com/downloads.html)

3. Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads)

4. Fork and clone this repo


### Running the VM

Follow these steps to launch the VM and organize a tournament.

1. Open a Git Bash shell and navigate to the newly created swiss_pairing 
directory. Note that on Linux or Mac you can use a regular 
terminal instead, but on Windows you will need to use the Git Bash shell.

    ```
    $ cd .../swisspairing/vagrant/swiss_pairing
    ```

2. Launch the VM and log in by typing:

    ```
    $ vagrant up
    $ vagrant ssh
    ```
    
3. Navigate to the swiss_pairing subdirectory:

    ```
    $ cd /vagrant/swiss_pairing
   ```
   
   This allows you to sync changes between the VM and the files on your 
   local machine.
   
4. At this point, you can set up the tournament database and hold a tournament.
See the next section, *Setup*, for further instructions.

5. When you're done using the Swiss pairing program, you can log out of the 
VM and shut it down by typing:

    ```
    ~$ exit
    ~$ vagrant halt
    ```
    


### Creating the database and running a tournament

Here are instructions for setting up the tournament database and holding a 
tournament. These steps assume you have logged in to the VM and navigated to
the swiss_pairing directory (i.e., Step 4 in the section *Running the VM*). 

1. Run the PostgreSQL script `tournament.sql` to 
create a database for storing tournament information:

    ```
    $ psql
    $ \i tournament.sql;
    $ \q
    ```
    This will start PostgreSQL, create a database called **tournament**, 
    then exit PostgreSQL. You can store multiple tournaments in the same 
    database, so this only needs to be done once.

2. Use functions in the module `tournament.py` to organize a new tournament and 
store the results in the **tournament** database. The script `run_tournament.py` 
shows two simulated tournament examples. You can run the examples like this: 

    ```
    $ python run_tournament.py
    ```
    
    It may be helpful to look at the function `simulateTournament` in `tournament.py`. 




### Features

* If there is a tie, each player gets 1 point. Otherwise, the winner gets 
2 points and the loser gets 0 points.
* There can be an odd number of players in a tournament. In this case, a 
different player gets a *bye* during each new round. Players that get a bye 
are given 1 point. Each player can have at most one bye round per tournament.
* A Swiss pairing system is used to match up players with comparable skill 
levels, but the program also makes sure that no two players get paired up 
more than once in a given tournament.
* The results from multiple tournaments can be stored in the same database.
* Data from a tournament is only saved if the tournament is succesfully 
completed. This prevents orphaned data from ending up in the database.


### To do

* A tournament can currently end in a tie. It would be good to create 
an option to prevent this.
* Low-scoring players are more likely to get a bye than high-scoring players.
There may be a better way to handle to process of assigning byes.
* There are a lot of functions in the file `tournament.py`. The code could 
use some refactoring.


### License

This project is released under [the MIT License](https://github.com/lmitchell4/alpha-blog/blob/master/LICENSE).




