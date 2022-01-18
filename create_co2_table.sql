CREATE TABLE co2emission_reduced (
    imo BIGINT PRIMARY KEY,
    ship_name VARCHAR(64) NOT NULL,
    type character varying(64) COLLATE pg_catalog."default" NOT NULL,
    issue date NOT NULL,
    expiry date NOT NULL,
    technical_efficiency_number REAL NOT NULL
);