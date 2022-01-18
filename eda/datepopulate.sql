INSERT INTO d_date
SELECT TO_CHAR(datum, 'yyyymmdd')::INT AS date_dim_id, --
       datum AS date_actual,
       EXTRACT(MONTH FROM datum)::INT AS month_actual,
       TO_CHAR(datum, 'TMMonth') AS month_name,
       TO_CHAR(datum, 'Mon') AS month_name_abbreviated,
       EXTRACT(QUARTER FROM datum) AS quarter_actual,
       CASE
           WHEN EXTRACT(QUARTER FROM datum) = 1 THEN 'Q1'
           WHEN EXTRACT(QUARTER FROM datum) = 2 THEN 'Q2'
           WHEN EXTRACT(QUARTER FROM datum) = 3 THEN 'Q3'
           WHEN EXTRACT(QUARTER FROM datum) = 4 THEN 'Q4'
           END AS quarter_name,
       EXTRACT(YEAR FROM datum)::INT AS year_actual,
       TO_CHAR(datum, 'mmyyyy')::CHAR(6) AS mmyyyy,
       TO_CHAR(datum, 'mmddyyyy')::CHAR(10) AS mmddyyyy
FROM (SELECT '2021-01-01'::DATE + SEQUENCE.DAY AS datum
      FROM GENERATE_SERIES(0, 550) AS SEQUENCE (DAY)
      GROUP BY SEQUENCE.DAY) DQ
ORDER BY 1;