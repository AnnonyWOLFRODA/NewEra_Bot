-- Table des structures
CREATE TABLE IF NOT EXISTS Structures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('Usine', 'Base', 'Ecole', 'Logement', 'Centrale', 'Technocentre')),
    specialization TEXT NOT NULL CHECK (specialization IN ('Terrestre', 'Aerienne', 'Navale', 'NA')),
    level INTEGER NOT NULL DEFAULT 1,
    capacity INTEGER DEFAULT 0 NOT NULL,  -- Capacité utile pour les logements/ecoles/bases
    population INTEGER DEFAULT 0 NOT NULL,  -- nb personnes affectées pour logements, bases, écoles, usines
    FOREIGN KEY (region_id) REFERENCES Regions(region_id)
        ON DELETE CASCADE
);
