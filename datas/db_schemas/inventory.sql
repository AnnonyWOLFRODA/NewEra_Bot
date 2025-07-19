-- Table de l’inventaire
CREATE TABLE IF NOT EXISTS Inventory (
    country_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0 NOT NULL,
    pol_points INTEGER DEFAULT 0 NOT NULL,
    diplo_points INTEGER DEFAULT 0 NOT NULL,
    soldiers INTEGER DEFAULT 0 NOT NULL,
    reserves INTEGER DEFAULT 0 NOT NULL,
    FOREIGN KEY (country_id) REFERENCES Countries(country_id)
        ON DELETE CASCADE
);

