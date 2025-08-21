
-- schema.sql (for reference / optional pre-run setup)
DROP TABLE IF EXISTS claims;
DROP TABLE IF EXISTS food_listings;
DROP TABLE IF EXISTS receivers;
DROP TABLE IF EXISTS providers;

CREATE TABLE providers (
    Provider_ID   INTEGER PRIMARY KEY,
    Name          VARCHAR(100) NOT NULL,
    Type          VARCHAR(50),
    Address       VARCHAR(255),
    City          VARCHAR(50),
    Contact       VARCHAR(50)
);

CREATE TABLE receivers (
    Receiver_ID   INTEGER PRIMARY KEY,
    Name          VARCHAR(100) NOT NULL,
    Type          VARCHAR(50),
    City          VARCHAR(50),
    Contact       VARCHAR(50)
);

CREATE TABLE food_listings (
    Food_ID       INTEGER PRIMARY KEY,
    Food_Name     VARCHAR(100) NOT NULL,
    Quantity      INTEGER NOT NULL,
    Expiry_Date   DATE NOT NULL,
    Provider_ID   INTEGER NOT NULL,
    Provider_Type VARCHAR(50),
    Location      VARCHAR(50),
    Food_Type     VARCHAR(50),
    Meal_Type     VARCHAR(50),
    FOREIGN KEY (Provider_ID) REFERENCES providers(Provider_ID) ON DELETE CASCADE
);

CREATE TABLE claims (
    Claim_ID     INTEGER PRIMARY KEY,
    Food_ID      INTEGER NOT NULL,
    Receiver_ID  INTEGER NOT NULL,
    Status       VARCHAR(20) NOT NULL,
    Timestamp    DATETIME NOT NULL,
    FOREIGN KEY (Food_ID) REFERENCES food_listings(Food_ID) ON DELETE CASCADE,
    FOREIGN KEY (Receiver_ID) REFERENCES receivers(Receiver_ID) ON DELETE CASCADE
);
