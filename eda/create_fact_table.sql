CREATE TABLE IF NOT EXISTS fact_table (
    imo BIGINT,
	fuel_consumption REAL,
	sea_time REAL,
	co2_distance REAL,
	co2_transport REAL,
	EEDI REAL,
	verifier_key BIGINT,
	ship_key BIGINT,
	issue_date_key BIGINT,
	expiry_date_key BIGINT
);