CREATE TABLE IF NOT EXISTS verifiers(
	verifier_key BIGINT  NOT NULL,
	verifier_name VARCHAR (128) NOT NULL,
	verifier_number VARCHAR (64) NOT NULL,
	verifier_nab VARCHAR (128) NOT NULL,
	verifier_address VARCHAR (128) NOT NULL,
	verifier_city VARCHAR (64) NOT NULL,
	verifier_country VARCHAR (64) NOT NULL
    );
