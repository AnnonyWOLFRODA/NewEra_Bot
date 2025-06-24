from abc import ABC, abstractmethod
import logging
from database import db_manager  # Import from database, not from bot

# Configure logger
logger = logging.getLogger("Economy")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class Item(ABC):
    @abstractmethod
    def get_amount(self, player_id: str) -> int:
        pass

    @abstractmethod
    def add(self, player_id: str, amount: int) -> None:
        pass

    @abstractmethod
    def remove(self, player_id: str, amount: int) -> None:
        pass

    @abstractmethod
    def set(self, player_id: str, amount: int) -> None:
        pass

    @abstractmethod
    def has_enough(self, player_id: str, amount: int) -> bool:
        pass

    @classmethod
    @abstractmethod
    def lead(cls, *args, **kwargs) -> list:
        pass

    @staticmethod
    @abstractmethod
    def pay_to(payer_id: str, receiver_id: str, amount: int, **kwargs) -> None:
        pass


class Currency(Item):
    def __init__(self, column: str):
        if column not in ["balance", "pol_points", "diplo_points"]:
            raise ValueError("Invalid column name")
        self.column = column  # e.g., "balance", "pol_points", "diplo_points"

    def get_amount(self, player_id: str) -> int:
        # Fetch the amount from the database
        
        result = db_manager.fetch(f"SELECT {self.column} FROM inventory WHERE player_id = ?", (player_id,))
        amt = result[0] if result else 0
        logger.debug(f"Get {self.column} for player {player_id}: {amt}")
        return amt

    def add(self, player_id: str, amount: int) -> None:
        result = self.get_amount(player_id)
        if result:
            new_amt = result[0] + amount
            #cur.execute(f"UPDATE inventory SET {self.column} = ? WHERE player_id = ?", (new_amt, player_id))
            db_manager.execute(f"UPDATE inventory SET {self.column} = ? WHERE player_id = ?", (new_amt, player_id))
        else:
            #cur.execute(f"INSERT INTO inventory (player_id, {self.column}) VALUES (?, ?)", (player_id, amount))
            db_manager.execute(f"INSERT INTO inventory (player_id, {self.column}) VALUES (?, ?)", (player_id, amount))
        logger.debug(f"Added {amount} to {self.column} for player {player_id}")

    def remove(self, player_id: str, amount: int) -> None:
        current = self.get_amount(player_id)
        new_amt = current - amount
        #cur.execute(f"UPDATE inventory SET {self.column} = ? WHERE player_id = ?", (new_amt, player_id))
        db_manager.execute(f"UPDATE inventory SET {self.column} = ? WHERE player_id = ?", (new_amt, player_id))
        logger.debug(f"Removed {amount} from {self.column} for player {player_id}")

    def set(self, player_id: str, amount: int) -> None:
        #cur.execute(f"SELECT {self.column} FROM inventory WHERE player_id = ?", (player_id,))
        result = self.get_amount(player_id)
        if result:
            #cur.execute(f"UPDATE inventory SET {self.column} = ? WHERE player_id = ?", (amount, player_id))
            db_manager.execute(f"UPDATE inventory SET {self.column} = ? WHERE player_id = ?", (amount, player_id))
        else:
            #cur.execute(f"INSERT INTO inventory (player_id, {self.column}) VALUES (?, ?)", (player_id, amount))
            db_manager.execute(f"INSERT INTO inventory (player_id, {self.column}) VALUES (?, ?)", (player_id, amount))
        logger.debug(f"Set {self.column} for player {player_id} to {amount}")

    def has_enough(self, player_id: str, amount: int) -> bool:
        result = self.get_amount(player_id) >= amount
        logger.debug(f"Player {player_id} has enough {self.column}? {result}")
        return result

    @classmethod
    def lead(cls, column: str) -> list:
        #cur.execute(f"SELECT player_id FROM inventory ORDER BY {column} DESC")
        rows = db_manager.fetch(f"SELECT player_id FROM inventory ORDER BY {column} DESC")
        leaders = [row[0] for row in rows]
        logger.debug(f"Leaderboard for {column}: {leaders}")
        return leaders

    @staticmethod
    def pay_to(payer_id: str, receiver_id: str, amount: int, column: str = "balance") -> None:
        curr = Currency(column)
        if not curr.has_enough(payer_id, amount):
            raise ValueError("Not enough funds")
        curr.remove(payer_id, amount)
        curr.add(receiver_id, amount)
        logger.debug(f"Paid {amount} in {column} from {payer_id} to {receiver_id}")


class Building(Item):
    def __init__(self, kind: str, level: int):
        # kind: e.g., "usine", "terrestre", "aerienne", etc.
        if kind not in ["usine", "terrestre", "aerienne", "maritime", "ecole"]:
            raise ValueError("Invalid building kind")
        if level < 1 or level > 7:
            raise ValueError("Invalid building level")
        self.kind = kind
        self.level = level

    def _column(self) -> str:
        return f"{self.kind}_{self.level}"

    def get_amount(self, player_id: str) -> int:
        column = self._column()
        #cur.execute(f"SELECT {column} FROM inventory WHERE player_id = ?", (player_id,))
        result = db_manager.fetch(f"SELECT {column} FROM inventory WHERE player_id = ?", (player_id,))
        amt = result[0] if result else 0
        logger.debug(f"Get building {column} for player {player_id}: {amt}")
        return amt

    def add(self, player_id: str, amount: int) -> None:
        column = self._column()
        # cur.execute(f"SELECT {column} FROM inventory WHERE player_id = ?", (player_id,))
        result = db_manager.fetch(f"SELECT {column} FROM inventory WHERE player_id = ?", (player_id,))
        if result:
            new_amt = result[0] + amount
            db_manager.execute(f"UPDATE inventory SET {column} = ? WHERE player_id = ?", (new_amt, player_id))
            #cur.execute(f"UPDATE inventory SET {column} = ? WHERE player_id = ?", (new_amt, player_id))
        else:
            # cur.execute(f"INSERT INTO inventory (player_id, {column}) VALUES (?, ?)", (player_id, amount))
            db_manager.execute(f"INSERT INTO inventory (player_id, {column}) VALUES (?, ?)", (player_id, amount))
        logger.debug(f"Added {amount} to building {column} for player {player_id}")

    def remove(self, player_id: str, amount: int) -> None:
        column = self._column()
        current = self.get_amount(player_id)
        new_amt = current - amount
        # cur.execute(f"UPDATE inventory SET {column} = ? WHERE player_id = ?", (new_amt, player_id))
        db_manager.execute(f"UPDATE inventory SET {column} = ? WHERE player_id = ?", (new_amt, player_id))
        logger.debug(f"Removed {amount} from building {column} for player {player_id}")

    def set(self, player_id: str, amount: int) -> None:
        column = self._column()
        # cur.execute(f"SELECT {column} FROM inventory WHERE player_id = ?", (player_id,))
        result = db_manager.fetch(f"SELECT {column} FROM inventory WHERE player_id = ?", (player_id,))
        if result:
            # cur.execute(f"UPDATE inventory SET {column} = ? WHERE player_id = ?", (amount, player_id))
            db_manager.execute(f"UPDATE inventory SET {column} = ? WHERE player_id = ?", (amount, player_id))
        else:
            # cur.execute(f"INSERT INTO inventory (player_id, {column}) VALUES (?, ?)", (player_id, amount))
            db_manager.execute(f"INSERT INTO inventory (player_id, {column}) VALUES (?, ?)", (player_id, amount))
        logger.debug(f"Set building {column} for player {player_id} to {amount}")

    def has_enough(self, player_id: str, amount: int) -> bool:
        current = self.get_amount(player_id)
        result = current >= amount
        logger.debug(f"Player {player_id} has enough building {self._column()}? {result}")
        return result

    @classmethod
    def lead(cls, kind: str, level: int) -> list:
        column = f"{kind}_{level}"
        # cur.execute(f"SELECT player_id FROM inventory ORDER BY {column} DESC")
        rows = db_manager.fetch(f"SELECT player_id FROM inventory ORDER BY {column} DESC")
        leaders = [row[0] for row in rows]
        logger.debug(f"Leaderboard for building {column}: {leaders}")
        return leaders

    @staticmethod
    def pay_to(payer_id: str, receiver_id: str, amount: int, kind: str, level: int) -> None:
        bld = Building(kind, level)
        if not bld.has_enough(payer_id, amount):
            raise ValueError("Not enough buildings to transfer")
        bld.remove(payer_id, amount)
        bld.add(receiver_id, amount)
        logger.debug(f"Transferred {amount} of building {kind}_{level} from {payer_id} to {receiver_id}")
