CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  portrait TEXT NOT NULL,
  buyOrders TEXT,
  sellOrders TEXT,
  access_token TEXT NOT NULL
);

CREATE TABLE structureAccess (
  id INTEGER NOT NULL,
  structure_id INTEGER NOT NULL,
  UNIQUE(id, structure_id)
);
