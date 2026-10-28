-- Small test data for business date 2026-10-07. Each block exercises one rule.

-- Mappings ---------------------------------------------------------------
INSERT INTO account_gl_map (map_id, account_id, gl_code, valid_from, valid_to) VALUES
  (1,  'A1',  'GL100', '2026-01-01', NULL),          -- many accounts -> one GL (A1, A2)
  (2,  'A2',  'GL100', '2026-01-01', NULL),
  (3,  'A3',  'GL200', '2026-01-01', NULL),          -- OVERLAP: A3 is also mapped to GL250 ...
  (4,  'A3',  'GL250', '2026-09-01', '2026-12-31'),  --  ... newer mapping should win
  (5,  'A4',  'GL300', '2026-01-01', '2026-10-06'),  -- expired the day before
  (6,  'A4',  'GL310', '2026-10-07', NULL),          -- starts on the business date (inclusive)
  (7,  'A5',  'GL400', '2026-01-01', '2026-10-07'),  -- ends on the business date (inclusive)
  (8,  'A7',  'GL500', '2026-01-01', NULL),          -- OVERLAP with identical dates and GL
  (9,  'A7',  'GL500', '2026-01-01', NULL),
  (10, 'A8',  'GL600', '2026-01-01', NULL),          -- GL with no GL-side row
  (11, 'A10', 'GL700', '2026-01-01', NULL),          -- difference of exactly 1.00
  (12, 'A11', 'GL710', '2026-01-01', NULL),          -- difference just over 1.00
  (13, 'A12', 'GL800', '2026-01-01', '2026-12-31'),  -- three rows for A12 that overlap each other
  (14, 'A12', 'GL810', '2026-06-01', '2026-09-30'),  --   (13,14) (13,15) (14,15) are all overlapping pairs
  (15, 'A12', 'GL820', '2026-08-01', NULL);
-- A6 and A9 have no mapping at all.

-- Source transactions -----------------------------------------------------
INSERT INTO stg_txn (source, txn_ref, account_id, business_date, amount_inr, dr_cr, file_id) VALUES
  ('CBS',   'T1',  'A1',  '2026-10-07', 1000.00, 'DR', 1),
  ('CBS',   'T2',  'A2',  '2026-10-07',  500.00, 'DR', 1),
  ('CBS',   'T3',  'A1',  '2026-10-07',  200.00, 'CR', 1),
  ('CARDS', 'C1',  'A3',  '2026-10-07',  300.00, 'DR', 2),
  ('LOANS', 'L1',  'A4',  '2026-10-07',  800.00, 'DR', 3),
  ('CBS',   'T5',  'A5',  '2026-10-07',  100.00, 'CR', 1),
  ('CBS',   'T6',  'A7',  '2026-10-07',  400.00, 'DR', 1),
  ('CBS',   'T9',  'A8',  '2026-10-07',   60.00, 'DR', 1),
  ('CBS',   'T11', 'A10', '2026-10-07',  100.00, 'DR', 1),
  ('CBS',   'T12', 'A11', '2026-10-07',  100.00, 'DR', 1),
  ('CBS',   'T7',  'A6',  '2026-10-07',  250.00, 'DR', 1),   -- unmapped
  ('CBS',   'T8',  'A6',  '2026-10-07',   50.00, 'CR', 1),   -- unmapped
  ('CARDS', 'C2',  'A9',  '2026-10-07',  150.00, 'DR', 2),   -- unmapped
  ('CBS',   'T10', 'A1',  '2026-10-06', 9999.00, 'DR', 1);   -- another day: must be ignored

-- GL totals ---------------------------------------------------------------
INSERT INTO gl_movement (gl_code, business_date, debit_total, credit_total, file_id) VALUES
  ('GL100', '2026-10-07', 1500.50, 200.00, 10),   -- 0.50 off: inside tolerance
  ('GL250', '2026-10-07',  300.00,   0.00, 10),
  ('GL310', '2026-10-07',  750.00,   0.00, 10),   -- 50.00 off: break
  ('GL400', '2026-10-07',    0.00, 100.00, 10),
  ('GL500', '2026-10-07',  400.00,   0.00, 10),
  ('GL700', '2026-10-07',  101.00,   0.00, 10),   -- exactly 1.00 off: matched
  ('GL710', '2026-10-07',  101.01,   0.00, 10),   -- 1.01 off: break
  ('GL999', '2026-10-07',   75.00,   0.00, 10),   -- GL side only
  ('GL100', '2026-10-06', 9999.00,   0.00, 9);    -- another day
