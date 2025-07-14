import sqlite3
from config import debug
import math


class Database:
    """Database class to handle database operations."""

    def __init__(self, path="datas/rts.db"):
        self.conn, self.cur = self.initialize_database()
        self.conn.row_factory = sqlite3.Row  # Enable row factory for dict-like access

    def __del__(self):
        if hasattr(self, "conn"):
            self.conn.close()

    def future_db(self):
        print(
        """ 
        CREATE TABLE IF NOT EXISTS Countries (
            country_id TEXT PRIMARY KEY,             -- Identifiant unique du pays
            name TEXT NOT NULL,                      -- Nom du pays
            public_channel_id TEXT NOT NULL,         -- ID du salon public (NON NULLABLE)
            secret_channel_id TEXT,                  -- ID du salon secret (NULLABLE)
            player_id TEXT                           -- ID du joueur qui contrôle le pays (NULL si aucun joueur)
        );
        CREATE TABLE IF NOT EXISTS Regions (
            region_id TEXT PRIMARY KEY,
            country_id TEXT NOT NULL,                  -- Pour rattacher la région à un pays
            name TEXT NOT NULL,                        -- Nom de la région
            population INTEGER DEFAULT 0 NOT NULL,
            FOREIGN KEY (country_id) REFERENCES Countries(country_id)
                ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS Inventory (
            country_id TEXT PRIMARY KEY,             -- Clé étrangère liée au pays
            balance INTEGER DEFAULT 0 NOT NULL,      -- Balance financière
            pol_points INTEGER DEFAULT 0 NOT NULL,   -- Points politiques
            diplo_points INTEGER DEFAULT 0 NOT NULL, -- Points diplomatiques
            soldiers INTEGER DEFAULT 0 NOT NULL,     -- Nombre de soldats actifs
            reserves INTEGER DEFAULT 0 NOT NULL,     -- Nombre de réservistes
            FOREIGN KEY (country_id) REFERENCES Countries(country_id)
                ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS Structures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region_id TEXT NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('Usine', 'Base', 'École')),
            specialization TEXT NOT NULL CHECK (specialization IN ('Terrestre', 'Aérienne', 'Navale')),
            level INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (region_id) REFERENCES Regions(region_id)
                ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS Stats (
            country_id TEXT PRIMARY KEY,              -- Clé étrangère liée au pays
            population INTEGER DEFAULT 0 NOT NULL,    -- Population totale
            population_capacity INTEGER DEFAULT 0 NOT NULL, -- Capacité d’accueil de la population
            tech_level INTEGER DEFAULT 1 NOT NULL,    -- Niveau technologique
            gdp INTEGER DEFAULT 0 NOT NULL,           -- Produit Intérieur Brut
            FOREIGN KEY (country_id) REFERENCES Countries(country_id)
                ON DELETE CASCADE
        );
        """
        )

    def initialize_database(self):
        """Initialize the database self.connection and create tables if they don't exist."""
        conn = sqlite3.connect("datas/rts.db", check_same_thread=False)
        cur = conn.cursor()

        # Create inventory table
        cur.execute(
            """
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
        """
        )
        conn.commit()

        if debug:
            # N.B for DB debug : Deleting the file won't work. You have to incode DROP the table & creating it back.
            cur.execute("PRAGMA table_info(inventory)")
            columns = cur.fetchall()
            cols = ["".join(str(tups)) for tups in columns]
            with open("db_test.logs", "w") as f:
                f.write("\n".join(cols) + "\n")
        return conn, cur

    def get_balance(self, player_id):
        """Get the balance of a player from the database."""
        self.cur.execute(
            "SELECT balance FROM inventory WHERE player_id = ?", (player_id,)
        )
        result = self.cur.fetchone()
        if result is not None:
            return str(result[0])
        return 0

    def get_points(self, player_id, type: int = 1):
        """Get the points of a player from the database."""
        if type == 1:
            self.cur.execute(
                "SELECT pol_points FROM inventory WHERE player_id = ?", (player_id,)
            )
        else:
            self.cur.execute(
                "SELECT diplo_points FROM inventory WHERE player_id = ?", (player_id,)
            )

        result = self.cur.fetchone()
        if result is not None:
            return result[0]
        else:
            return 0

    def has_enough_balance(self, player_id, amount):
        """Check if a player has enough balance."""
        self.cur.execute(
            "SELECT balance FROM inventory WHERE player_id = ?", (player_id,)
        )
        result = self.cur.fetchone()
        if result is None:
            return False
        if amount <= 0:
            return False
        return int(result[0]) >= int(amount)

    def has_enough_points(self, player_id, amount, type: int = 1):
        """Check if a player has enough points."""
        if type == 1:
            self.cur.execute(
                "SELECT pol_points FROM inventory WHERE player_id = ?", (player_id,)
            )
        else:
            self.cur.execute(
                "SELECT diplo_points FROM inventory WHERE player_id = ?", (player_id,)
            )
        result = self.cur.fetchone()
        if result is None:
            return False
        if amount <= 0:
            return False
        return result[0] >= amount

    def set_balance(self, player_id, amount):
        """Set the balance of a player."""
        self.cur.execute(
            "SELECT balance FROM inventory WHERE player_id = ?", (player_id,)
        )
        result = self.cur.fetchone()
        if result is not None:
            self.cur.execute(
                "UPDATE inventory SET balance = ? WHERE player_id = ?",
                (amount, player_id),
            )
        else:
            self.cur.execute(
                "INSERT INTO inventory (player_id, balance) VALUES (?, ?)",
                (player_id, amount),
            )
        self.conn.commit()

    def set_points(self, player_id, amount, type: int = 1):
        """Set the points of a player."""
        if type == 1:
            self.cur.execute(
                "SELECT pol_points FROM inventory WHERE player_id = ?", (player_id,)
            )
        else:
            self.cur.execute(
                "SELECT diplo_points FROM inventory WHERE player_id = ?", (player_id,)
            )
        result = self.cur.fetchone()
        if type == 1:
            if result is not None:
                self.cur.execute(
                    "UPDATE inventory SET pol_points = ? WHERE player_id = ?",
                    (amount, player_id),
                )
            else:
                self.cur.execute(
                    "INSERT INTO inventory (player_id, pol_points) VALUES (?, ?)",
                    (player_id, amount),
                )
        else:
            if result is not None:
                self.cur.execute(
                    "UPDATE inventory SET diplo_points = ? WHERE player_id = ?",
                    (amount, player_id),
                )
            else:
                self.cur.execute(
                    "INSERT INTO inventory (player_id, diplo_points) VALUES (?, ?)",
                    (player_id, amount),
                )
        self.conn.commit()

    def give_balance(self, player_id, amount):
        """Give money to a player."""
        self.cur.execute(
            "SELECT balance FROM inventory WHERE player_id = ?", (player_id,)
        )
        result = self.cur.fetchone()
        if result is not None:
            new_balance = result[0] + amount
            self.cur.execute(
                "UPDATE inventory SET balance = ? WHERE player_id = ?",
                (new_balance, player_id),
            )
        else:
            self.cur.execute(
                "INSERT INTO inventory (player_id, balance) VALUES (?, ?)",
                (player_id, amount),
            )
        self.conn.commit()

    def take_balance(self, player_id, amount):
        """Take money from a player."""
        self.cur.execute(
            "SELECT balance FROM inventory WHERE player_id = ?", (player_id,)
        )
        result = self.cur.fetchone()
        if result is not None:
            new_balance = result[0] - amount
            self.cur.execute(
                "UPDATE inventory SET balance = ? WHERE player_id = ?",
                (new_balance, player_id),
            )
        else:
            self.cur.execute(
                "INSERT INTO inventory (player_id, balance) VALUES (?, ?)",
                (player_id, -amount),
            )
        self.conn.commit()

    def give_points(self, player_id, amount, type: int = 1):
        """Give points to a player."""
        if type == 1:
            self.cur.execute(
                "SELECT pol_points FROM inventory WHERE player_id = ?", (player_id,)
            )
        else:
            self.cur.execute(
                "SELECT diplo_points FROM inventory WHERE player_id = ?", (player_id,)
            )
        result = self.cur.fetchone()
        if type == 1:
            if result is not None:
                new_points = result[0] + amount
                self.cur.execute(
                    "UPDATE inventory SET pol_points = ? WHERE player_id = ?",
                    (new_points, player_id),
                )
            else:
                self.cur.execute(
                    "INSERT INTO inventory (player_id, pol_points) VALUES (?, ?)",
                    (player_id, amount),
                )
        else:
            if result is not None:
                new_points = result[0] + amount
                self.cur.execute(
                    "UPDATE inventory SET diplo_points = ? WHERE player_id = ?",
                    (new_points, player_id),
                )
            else:
                self.cur.execute(
                    "INSERT INTO inventory (player_id, diplo_points) VALUES (?, ?)",
                    (player_id, amount),
                )

        self.conn.commit()

    def take_points(self, player_id, amount, type: int = 1):
        """Take points from a player."""
        if type == 1:
            self.cur.execute(
                "SELECT pol_points FROM inventory WHERE player_id = ?", (player_id,)
            )
        else:
            self.cur.execute(
                "SELECT diplo_points FROM inventory WHERE player_id = ?", (player_id,)
            )
        result = self.cur.fetchone()
        if type == 1:
            if result:
                new_balance = result[0] - amount
                self.cur.execute(
                    "UPDATE inventory SET pol_points = ? WHERE player_id = ?",
                    (new_balance, player_id),
                )
            else:
                self.cur.execute(
                    "INSERT INTO inventory (player_id, pol_points) VALUES (?, ?)",
                    (player_id, -amount),
                )
        else:
            if result:
                new_balance = result[0] - amount
                self.cur.execute(
                    "UPDATE inventory SET diplo_points = ? WHERE player_id = ?",
                    (new_balance, player_id),
                )
            else:
                self.cur.execute(
                    "INSERT INTO inventory (player_id, diplo_points) VALUES (?, ?)",
                    (player_id, -amount),
                )
        self.conn.commit()

    # Building-related database functions
    def get_usine(self, player_id, lvl, bat_type: int):
        """Get the number of buildings of a specific type and level owned by a player."""
        from config import bat_types

        self.cur.execute(
            f"SELECT {bat_types[bat_type][0]}{lvl} FROM inventory WHERE player_id = ?",
            (player_id,),
        )
        result = self.cur.fetchone()
        if result is not None:
            return int(result[0])
        else:
            return 0

    def has_enough_bats(self, player_id, amount, lvl, bat_type: int):
        """Check if a player has enough buildings of a specific type and level."""
        from config import bat_types

        self.cur.execute(
            f"SELECT {bat_types[bat_type][0]}{lvl} FROM inventory WHERE player_id = ?",
            (player_id,),
        )
        result = self.cur.fetchone()
        if result is None:
            return False
        if amount <= 0:
            return False
        return int(result[0]) >= int(amount)

    def give_usine(self, player_id, amount, lvl, bat_type: int):
        """Give buildings to a player."""
        from config import bat_types

        self.cur.execute(
            f"SELECT {bat_types[bat_type][0]}{lvl} FROM inventory WHERE player_id = ?",
            (player_id,),
        )
        result = self.cur.fetchone()
        if result is not None:
            new_balance = result[0] + amount
            self.cur.execute(
                f"UPDATE inventory SET {bat_types[bat_type][0]}{lvl} = ? WHERE player_id = ?",
                (new_balance, player_id),
            )
        else:
            self.cur.execute(
                f"INSERT INTO inventory (player_id, {bat_types[bat_type][0]}{lvl}) VALUES (?, ?)",
                (player_id, amount),
            )
        self.conn.commit()

    def set_usine(self, player_id, amount: int, lvl: int, bat_type: int):
        """Set the number of buildings of a specific type and level owned by a player."""
        from config import bat_types

        self.cur.execute(
            f"SELECT {bat_types[bat_type][0]}{lvl} FROM inventory WHERE player_id = ?",
            (player_id,),
        )
        result = self.cur.fetchone()
        if result is not None:
            self.cur.execute(
                f"UPDATE inventory SET {bat_types[bat_type][0]}{lvl} = ? WHERE player_id = ?",
                (amount, player_id),
            )
        else:
            self.cur.execute(
                f"INSERT INTO inventory (player_id, {bat_types[bat_type][0]}{lvl}) VALUES (?, ?)",
                (player_id, amount),
            )
        self.conn.commit()

    def remove_usine(self, player_id, amount: int, lvl: int, bat_type: int):
        """Remove buildings from a player."""
        from config import bat_types

        self.cur.execute(
            f"SELECT {bat_types[bat_type][0]}{lvl} FROM inventory WHERE player_id = ?",
            (player_id,),
        )
        result = self.cur.fetchone()
        if result is not None:
            new_balance = result[0] - amount
            self.cur.execute(
                f"UPDATE inventory SET {bat_types[bat_type][0]}{lvl} = ? WHERE player_id = ?",
                (new_balance, player_id),
            )
        else:
            self.cur.execute(
                f"INSERT INTO inventory (player_id, {bat_types[bat_type][0]}{lvl}) VALUES (?, ?)",
                (player_id, -amount),
            )
        self.conn.commit()

    def get_leads(self, lead_type: int, user_id: str):
        if lead_type == 1:
            self.cur.execute("SELECT player_id FROM inventory ORDER BY balance DESC")
        elif lead_type == 2:
            self.cur.execute("SELECT player_id FROM inventory ORDER BY pol_points DESC")
        elif lead_type == 3:
            self.cur.execute(
                "SELECT player_id FROM inventory ORDER BY diplo_points DESC"
            )
        elif lead_type == 4:
            self.cur.execute(
                "SELECT player_id FROM inventory ORDER BY (balance + pol_points + diplo_points) DESC"
            )
        leaderboard = self.cur.fetchall()
        leaderboard = [
            str(row[0]) for row in leaderboard
        ]  # Extraire uniquement les `player_id` dans une liste
        return (
            leaderboard.index(str(user_id)) + 1 if str(user_id) in leaderboard else -1
        )

    def lead_economy(self, size: int = 10):
        """Get the leaderboard of players based on their balance."""
        if size <= 0:
            self.cur.execute(
                "SELECT player_id, balance FROM inventory ORDER BY balance DESC"
            )
        else:
            self.cur.execute(
                "SELECT player_id, balance FROM inventory ORDER BY balance DESC LIMIT ?",
                (size,),
            )
        leaderboard = self.cur.fetchall()
        leaderboard = [(str(row[0]), int(row[1])) for row in leaderboard]
        return leaderboard

    def lead_pol(self, size: int = 10):
        """Get the leaderboard of players based on their political points."""
        if size <= 0:
            self.cur.execute(
                "SELECT player_id, pol_points FROM inventory ORDER BY pol_points DESC"
            )
        else:
            self.cur.execute(
                "SELECT player_id, pol_points FROM inventory ORDER BY pol_points DESC LIMIT ?",
                (size,),
            )
        leaderboard = self.cur.fetchall()
        leaderboard = [(str(row[0]), int(row[1])) for row in leaderboard]
        return leaderboard

    def lead_diplo(self, size: int = 10):
        """Get the leaderboard of players based on their diplomatic points."""
        if size <= 0:
            self.cur.execute(
                "SELECT player_id, diplo_points FROM inventory ORDER BY diplo_points DESC"
            )
        else:
            self.cur.execute(
                "SELECT player_id, diplo_points FROM inventory ORDER BY diplo_points DESC LIMIT ?",
                (size,),
            )
        leaderboard = self.cur.fetchall()
        leaderboard = [(str(row[0]), int(row[1])) for row in leaderboard]
        return leaderboard

    def lead_all(self, size: int = 10):
        """Get the leaderboard of players based on their total points (balance + political points + diplomatic points)."""
        if size <= 0:
            self.cur.execute(
                "SELECT player_id, balance + pol_points + diplo_points FROM inventory ORDER BY balance + pol_points + diplo_points DESC"
            )
        else:
            self.cur.execute(
                "SELECT player_id, balance + pol_points + diplo_points FROM inventory ORDER BY balance + pol_points + diplo_points DESC LIMIT ?",
                (size,),
            )
        leaderboard = self.cur.fetchall()
        leaderboard = [(str(row[0]), int(row[1])) for row in leaderboard]
        return leaderboard

    async def get_leaderboard(self, offset=0, limit=10):
        """Get the leaderboard of players based on their total points (balance + political points + diplomatic points)."""
        self.cur.execute(
            f"SELECT player_id, balance, pol_points, diplo_points FROM inventory ORDER BY (balance + pol_points + diplo_points) DESC LIMIT {limit} OFFSET {offset}"
        )
        return self.cur.fetchall()

    # Fonction pour calculer le temps de production
    def calculer_temps_production(
        self, player_id, appareil, quantite: int, app_type=None, production_data={}
    ):
        # Connexion à la base de données
        self.cur.execute("SELECT * FROM inventory WHERE player_id = ?", (player_id,))
        player_data = self.cur.fetchone()

        if not player_data:
            return f"Player ID {player_id} not found."

        # Définir un mapping pour les colonnes de la base de données
        columns = [
            "player_id",
            "balance",
            "pol_points",
            "diplo_points",
            "usine_lvl1",
            "usine_lvl2",
            "usine_lvl3",
            "usine_lvl4",
            "usine_lvl5",
            "usine_lvl6",
            "usine_lvl7",
            "population_caapcity",
        ]

        # Créer un dictionnaire des données du joueur
        player_inventory = dict(zip(columns, player_data))
        # Calculer la capacité de production totale par mois
        total_production_capacity = 0

        app_type = self.find_app_type(appareil, production_data)
        for i in range(1, 8):
            usine_lvl = f"usine_lvl{i}"
            usine_count = player_inventory[usine_lvl]
            if usine_count > 0:
                production_capacity = int(
                    production_data[str(i)]["production_mensuelle"][app_type][appareil]
                )
                total_production_capacity += production_capacity * usine_count

        if total_production_capacity == 0:
            return f"Player ID {player_id} has no production capacity for {appareil}."

        # Calculer le temps nécessaire pour produire la quantité demandée
        # return f"Quantite: {quantite}, total_production_capacity: {total_production_capacity}. Type appareil: {type(quantite)}, {type(total_production_capacity)}"
        time_needed_months = math.ceil(int(quantite) / int(total_production_capacity))

        return f"Pour produire {quantite} {appareil} (type {app_type}), il vous faudra {time_needed_months} mois. Vous avez une capacité de production totale de {total_production_capacity} par mois."

    def find_app_type(self, app_name, production_data={}):
        app_types = ["terrestre", "navale", "aerienne", "explosif"]

        for app_type in app_types:
            for apparel in production_data["7"]["production_mensuelle"][app_type]:
                if apparel.lower() == app_name.lower():
                    return app_type
        return None
    
    def leak_db(self):
        """Leak the database content, renvoie colonnes et lignes."""
        self.cur.execute("SELECT * FROM inventory")
        rows = self.cur.fetchall()
        columns = [desc[0] for desc in self.cur.description]
        return columns, rows
    
    def drop_all_except_inventory(db_path="datas/rts_clean.db"):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cur.fetchall()]
        tables_to_drop = [
            t for t in tables if t != "inventory" and not t.startswith("sqlite_")
        ]
        cur.execute("PRAGMA foreign_keys = OFF;")
        for table in tables_to_drop:
            print(f"Suppression de la table: {table}")
            cur.execute(f"DROP TABLE IF EXISTS {table};")
        cur.execute("PRAGMA foreign_keys = ON;")
        conn.commit()
        conn.close()
        print("Suppression terminée.")

