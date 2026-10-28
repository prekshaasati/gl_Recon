# Reconciliation platform: take-home

## Run it
```
pip install pytest
pytest                       # from the repository root: 68 tests, standard library only in src/

# SQL (optional, needs PostgreSQL): load the brief's schema and my sample data, then run a query
psql -f sql/test/schema.sql -f sql/test/sample_data.sql
psql -v business_date=2026-10-07 -f sql/b1_reconcile.sql
```
Layout: `design/` design document and diagrams, `sql/` the four queries, `src/gl_recon/` Python (one small file per job), `tests/`.
Import everything from the package: `from gl_recon import decide_file_action, validate_row, FileMeta, ...`.

## Decisions where the brief was silent

**decide_file_action** (rules checked in this order, first match wins)
- Reject a file with an unknown source, sequence below 1, or a blank checksum.
- A duplicate means the same checksum from the **same source**; identical bytes from two different sources are not duplicates.
- A corrected re-send always returns `LOAD_AND_RERUN_DATE`, because the old numbers are now wrong.
- A different file claiming the same source, date and sequence is `REJECT`: we cannot tell which is right, so a person decides.
- A supplementary file that arrives before the main file is `LOAD` with no rerun; the date is reconciled when the main file lands.
- File names are compared exactly (case-sensitive). Gaps in sequence numbers (2 missing, 3 arrives) are not checked.

**validate_row**
- Column names are matched exactly as written (no trimming, no case change). Values are trimmed.
- Check order, first problem wins: AMBIGUOUS_COLUMN, MISSING_FIELD, BAD_AMOUNT, BAD_DATE, DATE_MISMATCH, BAD_CURRENCY, BAD_DRCR.
- `txn_ref, account_id, business_date, amount, dr_cr` are always required, on top of the contract. Currency is required except for Loans.
- Amounts are digits only: no sign, comma, exponent, NaN or Infinity; zero is rejected. Rupees allow up to 2 decimals (the table stores 2). Paise must be whole numbers.
- Currency is case-insensitive (`inr` is accepted). Loans is always INR and any currency column is ignored.

**SQL**
- Mapping dates are inclusive. Overlaps: the latest `valid_from` wins, then the highest `map_id`.
- Tolerance is checked on debit and credit separately; a break is strictly more than 1.00. Difference is source minus GL.
- Unmapped transactions are a second result set in B1 (count, debit, credit, total).
- B3: an unchanged row keeps its old `run_id`; a GL code that disappears is deleted and logged with `new_status` NULL.
- B4: the grid covers every GL code ever in `recon_result` and every calendar day; the running total starts at the range start.

## With another day
- Run `validate_row` and `decide_file_action` inside a real loader (bulk load, transaction per file) and test it end to end.
- Add amount columns to `recon_change_log`, so an amount-only change is visible there.
- Handle a corrected re-send that changes the business date, and sequence gaps.
- Load-test the SQL at 50 million rows and add indexes or partitions from what the plans show.

## AI-use note
AI was used to generate senthetic test data and an AI tool solely to generate diagrams and visual representations based on the written content and technical explanations I had prepared. The underlying content, logic, and design decisions were my own.