--Q2 finding the overlapping mappings 
SELECT
    a.account_id,
    a.map_id AS map_id_1,
    a.gl_code AS gl_code_1,
    b.map_id AS map_id_2,
    b.gl_code AS gl_code_2
FROM account_gl_map a
JOIN account_gl_map b
    ON a.account_id = b.account_id
       AND a.map_id < b.map_id
WHERE
    (a.valid_to IS NULL OR b.valid_from <= a.valid_to)
       AND (b.valid_to IS NULL OR a.valid_from <= b.valid_to)
ORDER BY a.account_id;