-- B4: break trend for a date range.
-- Run with:  psql -v start_date=2026-10-01 -v end_date=2026-10-10 -f b4_break_trend.sql


WITH params AS (
    SELECT :'start_date'::date AS start_date,
:'end_date'::date   AS end_date
),

-- every date in the range.
days AS (
    SELECT d::date AS business_date
    FROM params,
generate_series(params.start_date, params.end_date, interval '1 day') AS d
),

-- every GL code we have ever reconciled.
gl_codes AS (
    SELECT DISTINCT gl_code FROM recon_result
),

-- the full grid, one row per GL code per date, whether or not a result exists.
grid AS (
    SELECT g.gl_code, d.business_date
    FROM gl_codes g
    CROSS JOIN days d
),

-- attach the break amount (0 when there is no row or the day matched).
daily AS (
    SELECT grid.gl_code,
grid.business_date,
    CASE WHEN r.status = 'BREAK'
        THEN ABS(r.src_debit - r.gl_debit) + ABS(r.src_credit - r.gl_credit)
        ELSE 0
        END::NUMERIC(18,2) AS break_amount
    FROM grid
    LEFT JOIN recon_result r
           ON r.gl_code = grid.gl_code
          AND r.business_date = grid.business_date
)

-- running total per GL code, in date order.
SELECT gl_code,
business_date,
break_amount,
    SUM(break_amount) OVER (
        PARTITION BY gl_code
        ORDER BY business_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
) AS running_total
    FROM daily
    ORDER BY gl_code, business_date;
