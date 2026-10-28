-- B1: reconcile one business date.
-- Run with:  psql -v business_date=2026-10-07 -f b1_reconcile.sql


--Q1
-- get business date as sql date object 
WITH params AS (
    SELECT :'business_date'::date AS d
),

-- get latest account_id and gl_code mapping (with latest validity takes precedence) to get one account per one gl mapping 
chosen_map AS ( SELECT DISTINCT ON (m.account_id) m.account_id, m.gl_code
FROM account_gl_map m, params p WHERE m.valid_from <= p.d AND (m.valid_to IS NULL OR m.valid_to >= p.d)
ORDER BY m.account_id, m.valid_from DESC, m.map_id DESC
),

-- get the total debit and credit amount for each Mapped GL codes in transaction of that date.
src AS (
    SELECT c.gl_code,
    SUM(CASE WHEN t.dr_cr = 'DR' THEN t.amount_inr ELSE 0 END) AS src_debit,
    SUM(CASE WHEN t.dr_cr = 'CR' THEN t.amount_inr ELSE 0 END) AS src_credit
FROM stg_txn t JOIN chosen_map c ON c.account_id = t.account_id WHERE t.business_date = (SELECT d FROM params)
    GROUP BY c.gl_code
),
-- get total debit and credit amount of GL from ledger of that date 
gl AS (
    SELECT g.gl_code, g.debit_total AS gl_debit, g.credit_total AS gl_credit FROM gl_movement g 
    WHERE g.business_date = (SELECT d FROM params)
),
-- full outer join on ledger and source query to get missing GL's data on each side . 
joined AS (
    SELECT COALESCE(s.gl_code, g.gl_code)               AS gl_code,
    COALESCE(s.src_debit, 0)::NUMERIC(18,2)      AS src_debit,
    COALESCE(s.src_credit, 0)::NUMERIC(18,2)     AS src_credit,
    COALESCE(g.gl_debit, 0)::NUMERIC(18,2)       AS gl_debit,
    COALESCE(g.gl_credit, 0)::NUMERIC(18,2)      AS gl_credit
    FROM src s FULL OUTER JOIN gl g ON g.gl_code = s.gl_code
)
-- using our outer joined table get credit_diff, debit_diff and break and match condition based on tolerence of 1 rupee
SELECT gl_code,src_debit,src_credit,gl_debit,gl_credit,src_debit  - gl_debit  AS debit_diff,
    src_credit - gl_credit AS credit_diff,
    CASE WHEN ABS(src_debit - gl_debit) > 1.00
        OR ABS(src_credit - gl_credit) > 1.00
        THEN 'BREAK' ELSE 'MATCHED' END AS status
FROM joined ORDER BY gl_code;

--Q2
--identify the account id where valid GL mapping is not present on the selected date
--and were left out in GL total as we calculate the total here 
WITH params AS (
    SELECT :'business_date'::date AS d
),
mapped_accounts AS (
    SELECT DISTINCT m.account_id
FROM account_gl_map m, params p WHERE m.valid_from <= p.d AND (m.valid_to IS NULL OR m.valid_to >= p.d)
)
SELECT COUNT(*)  AS unmapped_txn_count,
    COUNT(DISTINCT t.account_id) AS unmapped_account_count,
    COALESCE(SUM(CASE WHEN t.dr_cr = 'DR' THEN t.amount_inr END), 0)::NUMERIC(18,2) AS unmapped_debit,
    COALESCE(SUM(CASE WHEN t.dr_cr = 'CR' THEN t.amount_inr END), 0)::NUMERIC(18,2) AS unmapped_credit,
    COALESCE(SUM(t.amount_inr), 0)::NUMERIC(18,2) AS unmapped_total_amount
FROM stg_txn t
LEFT JOIN mapped_accounts a ON a.account_id = t.account_id
WHERE t.business_date = (SELECT d FROM params) AND a.account_id IS NULL;