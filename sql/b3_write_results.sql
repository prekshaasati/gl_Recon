-- B3: write results safely.
-- Run with:  psql -v business_date=2026-10-07 -v run_id=101 -f b3_write_results.sql

\set ON_ERROR_STOP on
BEGIN;

-- Step 1: sAVE B1 query result into Temp table 
CREATE TEMP TABLE new_result ON COMMIT DROP AS
WITH params AS (
    SELECT :'business_date'::date AS d
),
chosen_map AS (
    SELECT DISTINCT ON (m.account_id) m.account_id, m.gl_code
FROM account_gl_map m, params p
WHERE m.valid_from <= p.d
      AND (m.valid_to IS NULL OR m.valid_to >= p.d)
ORDER BY m.account_id, m.valid_from DESC, m.map_id DESC
),
src AS (
    SELECT c.gl_code,
    SUM(CASE WHEN t.dr_cr = 'DR' THEN t.amount_inr ELSE 0 END) AS src_debit,
    SUM(CASE WHEN t.dr_cr = 'CR' THEN t.amount_inr ELSE 0 END) AS src_credit
    FROM stg_txn t
    JOIN chosen_map c ON c.account_id = t.account_id
    WHERE t.business_date = (SELECT d FROM params)
    GROUP BY c.gl_code
),
gl AS (
    SELECT g.gl_code, g.debit_total AS gl_debit, g.credit_total AS gl_credit
    FROM gl_movement g
    WHERE g.business_date = (SELECT d FROM params)
),
joined AS (
    SELECT COALESCE(s.gl_code, g.gl_code)           AS gl_code,
    COALESCE(s.src_debit, 0)::NUMERIC(18,2)  AS src_debit,
    COALESCE(s.src_credit, 0)::NUMERIC(18,2) AS src_credit,
    COALESCE(g.gl_debit, 0)::NUMERIC(18,2)   AS gl_debit,
    COALESCE(g.gl_credit, 0)::NUMERIC(18,2)  AS gl_credit
    FROM src s
    FULL OUTER JOIN gl g ON g.gl_code = s.gl_code
)
SELECT (SELECT d FROM params) AS business_date,
gl_code, src_debit, src_credit, gl_debit, gl_credit,
    CASE WHEN ABS(src_debit - gl_debit) > 1.00
      OR ABS(src_credit - gl_credit) > 1.00
      THEN 'BREAK' ELSE 'MATCHED' END AS status
FROM joined;

-- Step 2: write the change log FIRST, while the old values are still in recon_result.
--Checks the old and new reconciliation results and saves a record whenever the amounts or status have changed.

INSERT INTO recon_change_log (run_id, business_date, gl_code, old_status, new_status)
    SELECT :run_id,
    COALESCE(n.business_date, o.business_date),
    COALESCE(n.gl_code, o.gl_code),
    o.status,
    n.status
    FROM new_result n
FULL OUTER JOIN (SELECT * FROM recon_result WHERE business_date = :'business_date'::date) o---- FULL JOIN of old vs new finds new, changed and removed GL codes in one pass.
  ON  o.business_date = n.business_date
      AND o.gl_code       = n.gl_code
WHERE (o.src_debit, o.src_credit, o.gl_debit, o.gl_credit, o.status)
      IS DISTINCT FROM
      (n.src_debit, n.src_credit, n.gl_debit, n.gl_credit, n.status);

-- Step 3: insert new rows and update changed rows. The WHERE clause on the update
-- means an identical row is left completely alone (and keeps its old run_id).
INSERT INTO recon_result
(business_date, gl_code, src_debit, src_credit, gl_debit, gl_credit, status, run_id)
    SELECT business_date, gl_code, src_debit, src_credit, gl_debit, gl_credit, status, :run_id
FROM new_result
ON CONFLICT (business_date, gl_code) DO UPDATE
    SET src_debit  = EXCLUDED.src_debit,
    src_credit = EXCLUDED.src_credit,
    gl_debit   = EXCLUDED.gl_debit,
    gl_credit  = EXCLUDED.gl_credit,
    status     = EXCLUDED.status,
    run_id     = EXCLUDED.run_id
WHERE (recon_result.src_debit, recon_result.src_credit, recon_result.gl_debit,
recon_result.gl_credit, recon_result.status)
      IS DISTINCT FROM
    (EXCLUDED.src_debit, EXCLUDED.src_credit, EXCLUDED.gl_debit,
      EXCLUDED.gl_credit, EXCLUDED.status);

-- Step 4: remove GL codes that no longer appear for this date.
DELETE FROM recon_result r
WHERE r.business_date = :'business_date'::date
    AND NOT EXISTS (SELECT 1 FROM new_result n WHERE n.gl_code = r.gl_code);

COMMIT;