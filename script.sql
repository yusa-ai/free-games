CREATE TABLE IF NOT EXISTS channels (
    id INT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS deals (
    id TEXT,
    channel_id INT REFERENCES channels (id),
    PRIMARY KEY (id, channel_id)
);

CREATE TABLE IF NOT EXISTS stores (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

INSERT OR IGNORE INTO stores VALUES ("1", "Steam");
INSERT OR IGNORE INTO stores VALUES ("7", "GOG");
INSERT OR IGNORE INTO stores VALUES ("8", "Origin");
INSERT OR IGNORE INTO stores VALUES ("13", "Ubisoft Connect");
INSERT OR IGNORE INTO stores VALUES ("15", "Fanatical");
INSERT OR IGNORE INTO stores VALUES ("25", "the Epic Games Store");
