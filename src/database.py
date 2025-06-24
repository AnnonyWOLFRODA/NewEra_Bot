import aiosqlite
import logging

logger = logging.getLogger("Database")

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
        
    async def connect(self):
        logger.info(f"Connecting to database at {self.db_path}")
        self.connection = await aiosqlite.connect(self.db_path)
        await self._initialize_tables()
        
    async def _initialize_tables(self):
        # Create necessary tables if they don't exist
        await self.connection.execute("""
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
        await self.connection.commit()
        
    async def fetch(self, query: str, params=()):
        if not self.connection:
            raise RuntimeError("Database not connected")
        async with self.connection.execute(query, params) as cursor:
            return await cursor.fetchall()
            
    async def execute(self, query: str, params=()):
        if not self.connection:
            raise RuntimeError("Database not connected")
        await self.connection.execute(query, params)
        await self.connection.commit()
        
    async def close(self):
        if self.connection:
            await self.connection.close()

# Create a global instance - but don't connect yet
db_manager = None
