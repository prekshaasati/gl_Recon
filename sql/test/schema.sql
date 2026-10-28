-- The schema from the brief, unchanged. Used only to test the queries locally.
DROP TABLE IF EXISTS recon_change_log, recon_result, gl_movement, account_gl_map, stg_txn CASCADE;

CREATE TABLE stg_txn (
  source        TEXT          NOT NULL,
  txn_ref       TEXT          NOT NULL,
  account_id    TEXT          NOT NULL,
  business_date DATE          NOT NULL,
  amount_inr    NUMERIC(18,2) NOT NULL CHECK (amount_inr > 0),
  dr_cr         CHAR(2)       NOT NULL CHECK (dr_cr IN ('DR','CR')),
  file_id       BIGINT        NOT NULL,
  PRIMARY KEY (source, txn_ref)
);

CREATE TABLE account_gl_map (
  map_id      BIGINT PRIMARY KEY,
  account_id  TEXT NOT NULL,
  gl_code     TEXT NOT NULL,
  valid_from  DATE NOT NULL,
  valid_to    DATE
);

CREATE TABLE gl_movement (
  gl_code       TEXT          NOT NULL,
  business_date DATE          NOT NULL,
  debit_total   NUMERIC(18,2) NOT NULL,
  credit_total  NUMERIC(18,2) NOT NULL,
  file_id       BIGINT        NOT NULL,
  PRIMARY KEY (gl_code, business_date)
);

CREATE TABLE recon_result (
  business_date DATE          NOT NULL,
  gl_code       TEXT          NOT NULL,
  src_debit     NUMERIC(18,2) NOT NULL,
  src_credit    NUMERIC(18,2) NOT NULL,
  gl_debit      NUMERIC(18,2) NOT NULL,
  gl_credit     NUMERIC(18,2) NOT NULL,
  status        TEXT          NOT NULL,
  run_id        BIGINT        NOT NULL,
  PRIMARY KEY (business_date, gl_code)
);

CREATE TABLE recon_change_log (
  run_id        BIGINT      NOT NULL,
  business_date DATE        NOT NULL,
  gl_code       TEXT        NOT NULL,
  old_status    TEXT,
  new_status    TEXT,
  changed_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
