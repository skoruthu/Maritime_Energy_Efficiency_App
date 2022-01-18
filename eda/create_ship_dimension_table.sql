CREATE TABLE IF NOT EXISTS ship_dimension(
	ship_key BIGINT NOT NULL,
	ship_name VARCHAR(64),
	ship_type VARCHAR(64),
	call_sign VARCHAR(10) NOT NULL,
	speed REAL NOT NULL,
	year_built INT NOT NULL,
	length REAL NOT NULL,
	width REAL NOT NULL,
	tonnage REAL NOT NULL,
	engine_type VARCHAR(64) NOT NULL,
	mmsi BIGINT NOT NULL
    );