CREATE TABLE IF NOT EXISTS channels (
    id INT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS deals (
                                     id         TEXT,
                                     channel_id INT REFERENCES channels (id),
                                     PRIMARY KEY (id, channel_id)
);

CREATE TABLE IF NOT EXISTS stores
(
    id   TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS channel_stores
(
    channel_id INT REFERENCES channels (id),
    store_id   TEXT REFERENCES stores (id),
    PRIMARY KEY (channel_id, store_id)
);

INSERT OR IGNORE INTO stores
VALUES ("1", "Steam");
INSERT OR IGNORE INTO stores
VALUES ("7", "GOG");
INSERT OR IGNORE INTO stores
VALUES ("8", "Origin");
INSERT OR IGNORE INTO stores
VALUES ("13", "Ubisoft Connect");
INSERT OR IGNORE INTO stores
VALUES ("15", "Fanatical");
INSERT OR IGNORE INTO stores
VALUES ("25", "Epic Games Store");
