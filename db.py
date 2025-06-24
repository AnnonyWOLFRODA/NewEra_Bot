import sqlite3
from config import debug

def initialize_database():
    """Initialize the database connection and create tables if they don't exist."""
    conn = sqlite3.connect('datas/rts.db', check_same_thread=False)
    cur = conn.cursor()
    
    # Create inventory table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            player_id TEXT PRIMARY KEY,
            balance INTEGER DEFAULT 0 NOT NULL,
            pol_points INTEGER DEFAULT 0 NOT NULL,
            diplo_points INTEGER DEFAULT 0 NOT NULL,
            usine_lvl1 INTEGER DEFAULT 0 NOT NULL,
            usine_lvl2 INTEGER DEFAULT 0 NOT NULL,
            usine_lvl3 INTEGER DEFAULT 0 NOT NULL,
            usine_lvl4 INTEGER DEFAULT 0 NOT NULL,
            usine_lvl5 INTEGER DEFAULT 0 NOT NULL,
            usine_lvl6 INTEGER DEFAULT 0 NOT NULL,
            usine_lvl7 INTEGER DEFAULT 0 NOT NULL,
            terrestre_1 INTEGER DEFAULT 0 NOT NULL,
            terrestre_2 INTEGER DEFAULT 0 NOT NULL,
            terrestre_3 INTEGER DEFAULT 0 NOT NULL,
            terrestre_4 INTEGER DEFAULT 0 NOT NULL,
            terrestre_5 INTEGER DEFAULT 0 NOT NULL,
            terrestre_6 INTEGER DEFAULT 0 NOT NULL,
            terrestre_7 INTEGER DEFAULT 0 NOT NULL,
            aerienne_1 INTEGER DEFAULT 0 NOT NULL,
            aerienne_2 INTEGER DEFAULT 0 NOT NULL,
            aerienne_3 INTEGER DEFAULT 0 NOT NULL,
            aerienne_4 INTEGER DEFAULT 0 NOT NULL,
            maritime_1 INTEGER DEFAULT 0 NOT NULL,
            maritime_2 INTEGER DEFAULT 0 NOT NULL,
            maritime_3 INTEGER DEFAULT 0 NOT NULL,
            maritime_4 INTEGER DEFAULT 0 NOT NULL,
            ecole_1 INTEGER DEFAULT 0 NOT NULL,
            ecole_2 INTEGER DEFAULT 0 NOT NULL,
            ecole_3 INTEGER DEFAULT 0 NOT NULL,
            ecole_4 INTEGER DEFAULT 0 NOT NULL,
            population_capacity INTEGER DEFAULT 0 NOT NULL
        )
    """)
    conn.commit()
    
    if debug:
        # N.B for DB debug : Deleting the file won't work. You have to incode DROP the table & creating it back.
        cur.execute("PRAGMA table_info(inventory)")
        columns = cur.fetchall()
        cols = [''.join(str(tups)) for tups in columns]
        with open("db_test.logs", "w") as f:
            f.write("\n".join(cols) + '\n')
        return conn, cur

    def get_balance(player_id):
        """Get the balance of a player from the database."""
        cur.execute("SELECT balance FROM inventory WHERE player_id = ?", (player_id,))
        result = cur.fetchone()
        if result is not None:
            return str(result[0])
        return 0

    def get_points(player_id, type:int=1):
        """Get the points of a player from the database."""
        if type == 1:
            cur.execute("SELECT pol_points FROM inventory WHERE player_id = ?", (player_id,))
        else:
            cur.execute("SELECT diplo_points FROM inventory WHERE player_id = ?", (player_id,))

        result = cur.fetchone()
        if result is not None:
            return result[0]
        else:
            return 0

    def has_enough_balance(player_id, amount):
        """Check if a player has enough balance."""
        cur.execute("SELECT balance FROM inventory WHERE player_id = ?", (player_id,))
        result = cur.fetchone()
        if result is None:
            return False
        if amount <= 0:
            return False
        return int(result[0]) >= int(amount)

    def has_enough_points(player_id, amount, type:int=1):
        """Check if a player has enough points."""
        if type == 1:
            cur.execute("SELECT pol_points FROM inventory WHERE player_id = ?", (player_id,))
        else:
            cur.execute("SELECT diplo_points FROM inventory WHERE player_id = ?", (player_id,))
        result = cur.fetchone()
        if result is None:
            return False
        if amount <= 0:
            return False
        return result[0] >= amount

    def set_balance_func(player_id, amount):
        """Set the balance of a player."""
        cur.execute("SELECT balance FROM inventory WHERE player_id = ?", (player_id,))
        result = cur.fetchone()
        if result is not None:
            cur.execute("UPDATE inventory SET balance = ? WHERE player_id = ?", (amount, player_id))
        else:
            cur.execute("INSERT INTO inventory (player_id, balance) VALUES (?, ?)", (player_id, amount))
        conn.commit()

    def set_points_func(player_id, amount, type:int=1):
        """Set the points of a player."""
        if type == 1:
            cur.execute("SELECT pol_points FROM inventory WHERE player_id = ?", (player_id,))
        else:
            cur.execute("SELECT diplo_points FROM inventory WHERE player_id = ?", (player_id,))
        result = cur.fetchone()
        if type == 1:
            if result is not None:
                cur.execute("UPDATE inventory SET pol_points = ? WHERE player_id = ?", (amount, player_id))
            else:
                cur.execute("INSERT INTO inventory (player_id, pol_points) VALUES (?, ?)", (player_id, amount))
        else:
            if result is not None:
                cur.execute("UPDATE inventory SET diplo_points = ? WHERE player_id = ?", (amount, player_id))
            else:
                cur.execute("INSERT INTO inventory (player_id, diplo_points) VALUES (?, ?)", (player_id, amount))
        conn.commit()

    def give_money(player_id, amount):
        """Give money to a player."""
        cur.execute("SELECT balance FROM inventory WHERE player_id = ?", (player_id,))
        result = cur.fetchone()
        if result is not None:
            new_balance = result[0] + amount
            cur.execute("UPDATE inventory SET balance = ? WHERE player_id = ?", (new_balance, player_id))
        else:
            cur.execute("INSERT INTO inventory (player_id, balance) VALUES (?, ?)", (player_id, amount))
        conn.commit()

    def take_money_func(player_id, amount):
        """Take money from a player."""
        cur.execute("SELECT balance FROM inventory WHERE player_id = ?", (player_id,))
        result = cur.fetchone()
        if result is not None:
            new_balance = result[0] - amount
            cur.execute("UPDATE inventory SET balance = ? WHERE player_id = ?", (new_balance, player_id))
        else:
            cur.execute("INSERT INTO inventory (player_id, balance) VALUES (?, ?)", (player_id, -amount))
        conn.commit()

    def give_points(player_id, amount, type:int=1):
        """Give points to a player."""
        if type == 1:
            cur.execute("SELECT pol_points FROM inventory WHERE player_id = ?", (player_id,))
        else:
            cur.execute("SELECT diplo_points FROM inventory WHERE player_id = ?", (player_id,))
        result = cur.fetchone()
        if type == 1:
            if result is not None:
                new_points = result[0] + amount
                cur.execute("UPDATE inventory SET pol_points = ? WHERE player_id = ?", (new_points, player_id))
            else:
                cur.execute("INSERT INTO inventory (player_id, pol_points) VALUES (?, ?)", (player_id, amount))
        else:
            if result is not None:
                new_points = result[0] + amount
                cur.execute("UPDATE inventory SET diplo_points = ? WHERE player_id = ?", (new_points, player_id))
            else:
                cur.execute("INSERT INTO inventory (player_id, diplo_points) VALUES (?, ?)", (player_id, amount))

        conn.commit()

    def take_points_func(player_id, amount, type:int=1):
        """Take points from a player."""
        if type == 1:
            cur.execute("SELECT pol_points FROM inventory WHERE player_id = ?", (player_id,))
        else:
            cur.execute("SELECT diplo_points FROM inventory WHERE player_id = ?", (player_id,))
        result = cur.fetchone()
        if type == 1:
            if result:
                new_balance = result[0] - amount
                cur.execute("UPDATE inventory SET pol_points = ? WHERE player_id = ?", (new_balance, player_id))
            else:
                cur.execute("INSERT INTO inventory (player_id, pol_points) VALUES (?, ?)", (player_id, -amount))
        else:
            if result:
                new_balance = result[0] - amount
                cur.execute("UPDATE inventory SET diplo_points = ? WHERE player_id = ?", (new_balance, player_id))
            else:
                cur.execute("INSERT INTO inventory (player_id, diplo_points) VALUES (?, ?)", (player_id, -amount))
        conn.commit()

    # Building-related database functions
    def get_usine(player_id, lvl, bat_type:int):
        """Get the number of buildings of a specific type and level owned by a player."""
        from config import bat_types
        cur.execute(f"SELECT {bat_types[bat_type][0]}{lvl} FROM inventory WHERE player_id = ?", (player_id,))
        result = cur.fetchone()
        if result is not None:
            return int(result[0])
        else:
            return 0

    def has_enough_bats(player_id, amount, lvl, bat_type:int):
        """Check if a player has enough buildings of a specific type and level."""
        from config import bat_types
        cur.execute(f"SELECT {bat_types[bat_type][0]}{lvl} FROM inventory WHERE player_id = ?", (player_id,))
        result = cur.fetchone()
        if result is None:
            return False
        if amount <= 0:
            return False
        return int(result[0]) >= int(amount)

    def give_usine(player_id, amount, lvl, bat_type:int):
        """Give buildings to a player."""
        from config import bat_types
        cur.execute(f"SELECT {bat_types[bat_type][0]}{lvl} FROM inventory WHERE player_id = ?", (player_id,))
        result = cur.fetchone()
        if result is not None:
            new_balance = result[0] + amount
            cur.execute(f"UPDATE inventory SET {bat_types[bat_type][0]}{lvl} = ? WHERE player_id = ?", (new_balance, player_id))
        else:
            cur.execute(f"INSERT INTO inventory (player_id, {bat_types[bat_type][0]}{lvl}) VALUES (?, ?)", (player_id, amount))
        conn.commit()

    def set_usine_func(player_id, amount: int, lvl: int, bat_type:int):
        """Set the number of buildings of a specific type and level owned by a player."""
        from config import bat_types
        cur.execute(f"SELECT {bat_types[bat_type][0]}{lvl} FROM inventory WHERE player_id = ?", (player_id,))
        result = cur.fetchone()
        if result is not None:
            cur.execute(f"UPDATE inventory SET {bat_types[bat_type][0]}{lvl} = ? WHERE player_id = ?", (amount, player_id))
        else:
            cur.execute(f"INSERT INTO inventory (player_id, {bat_types[bat_type][0]}{lvl}) VALUES (?, ?)", (player_id, amount))
        conn.commit()

    def remove_usine_func(player_id, amount: int, lvl: int, bat_type:int):
        """Remove buildings from a player."""
        from config import bat_types
        cur.execute(f"SELECT {bat_types[bat_type][0]}{lvl} FROM inventory WHERE player_id = ?", (player_id,))
        result = cur.fetchone()
        if result is not None:
            new_balance = result[0] - amount
            cur.execute(f"UPDATE inventory SET {bat_types[bat_type][0]}{lvl} = ? WHERE player_id = ?", (new_balance, player_id))
        else:
            cur.execute(f"INSERT INTO inventory (player_id, {bat_types[bat_type][0]}{lvl}) VALUES (?, ?)", (player_id, -amount))
        conn.commit()
    
    def get_leads(lead_type: int, user_id: str):
        if lead_type == 1:
            cur.execute("SELECT player_id FROM inventory ORDER BY balance DESC")
        elif lead_type == 2:
            cur.execute("SELECT player_id FROM inventory ORDER BY pol_points DESC")
        elif lead_type == 3:
            cur.execute("SELECT player_id FROM inventory ORDER BY diplo_points DESC")
        elif lead_type == 4:
            cur.execute("SELECT player_id FROM inventory ORDER BY (balance + pol_points + diplo_points) DESC")
        leaderboard = cur.fetchall()
        leaderboard = [str(row[0]) for row in leaderboard]  # Extraire uniquement les `player_id` dans une liste    
        return leaderboard.index(str(user_id)) + 1 if str(user_id) in leaderboard else -1


    def lead_economy(size:int=10):
        """Get the leaderboard of players based on their balance."""
        if size <= 0:
            cur.execute("SELECT player_id, balance FROM inventory ORDER BY balance DESC")
        else:
            cur.execute("SELECT player_id, balance FROM inventory ORDER BY balance DESC LIMIT ?", (size,))
        leaderboard = cur.fetchall()
        leaderboard = [(str(row[0]), int(row[1])) for row in leaderboard]
        return leaderboard
    
    def lead_pol(size:int=10):
        """Get the leaderboard of players based on their political points."""
        if size <= 0:
            cur.execute("SELECT player_id, pol_points FROM inventory ORDER BY pol_points DESC")
        else:
            cur.execute("SELECT player_id, pol_points FROM inventory ORDER BY pol_points DESC LIMIT ?", (size,))
        leaderboard = cur.fetchall()
        leaderboard = [(str(row[0]), int(row[1])) for row in leaderboard]
        return leaderboard
    def lead_diplo(size:int=10):
        """Get the leaderboard of players based on their diplomatic points."""
        if size <= 0:
            cur.execute("SELECT player_id, diplo_points FROM inventory ORDER BY diplo_points DESC")
        else:
            cur.execute("SELECT player_id, diplo_points FROM inventory ORDER BY diplo_points DESC LIMIT ?", (size,))
        leaderboard = cur.fetchall()
        leaderboard = [(str(row[0]), int(row[1])) for row in leaderboard]
        return leaderboard

    def lead_all(size:int=10):
        """Get the leaderboard of players based on their total points (balance + political points + diplomatic points)."""
        if size <= 0:
            cur.execute("SELECT player_id, balance + pol_points + diplo_points FROM inventory ORDER BY balance + pol_points + diplo_points DESC")
        else:
            cur.execute("SELECT player_id, balance + pol_points + diplo_points FROM inventory ORDER BY balance + pol_points + diplo_points DESC LIMIT ?", (size,))
        leaderboard = cur.fetchall()
        leaderboard = [(str(row[0]), int(row[1])) for row in leaderboard]
        return leaderboard