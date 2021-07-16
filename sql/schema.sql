CREATE TABLE users (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  profile_pic TEXT NOT NULL,
  buyOrders TEXT,
  sellOrders TEXT,
  access_token TEXT NOT NULL
);

CREATE TABLE structures (
  id TEXT NOT NULL,
  structure_id TEXT NOT NULL
);
