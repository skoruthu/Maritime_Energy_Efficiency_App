-- add primary key on imo in ship table
ALTER TABLE ship_dimension
ADD PRIMARY KEY (ship_key);

-- add primary key on verifier name
ALTER TABLE verifiers
ADD PRIMARY KEY (verifier_key);

-- changed primary key
ALTER TABLE d_date
ADD PRIMARY KEY (date_dim_id);

-- add foreign key on date in fact_table
ALTER TABLE fact_table
ADD FOREIGN KEY (issue_date_key) REFERENCES d_date(date_dim_id);

ALTER TABLE fact_table
ADD FOREIGN KEY (expiry_date_key) REFERENCES d_date(date_dim_id);

-- add foreign key on verifier_key
ALTER TABLE fact_table
ADD FOREIGN KEY (verifier_key) REFERENCES verifiers(verifier_key);

-- add foreign key on ship_key
ALTER TABLE fact_table
ADD FOREIGN KEY (ship_key) REFERENCES ship_dimension(ship_key);


