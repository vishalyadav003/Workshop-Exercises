# Security Test Notes

## SQL injection protection

Every application query that accepts data binds values through SQLite's `?` placeholders. SQL strings contain only fixed statements and fixed identifiers; caller data is not interpolated with f-strings, `%`, or concatenation. The payload `' OR '1'='1` supplied as a status fails the application allowlist. The same text in an issue description is inserted and read back literally, demonstrating that it remains data rather than changing the query predicate.

## Validation and database constraints

- Required text is stripped and rejected when empty before insertion.
- Statuses are allowlisted in Python and constrained again by table `CHECK` clauses.
- Duplicate primary keys are rejected by SQLite; foreign keys reject nonexistent equipment, technician, or request references.
- Maintenance costs cannot be negative. Closed requests require `resolved_at`; non-closed requests require it to be null.
- Query filters are parameterized; only fixed SQL identifiers and fixed report expressions are present in query text.

## Demonstration coverage

Run `python main.py`. The program attempts a duplicate equipment primary key, an invalid status, a blank equipment name, and an injection-shaped status filter, reporting each expected rejection. It then stores an injection-shaped issue description literally. A simulated `sqlite3.OperationalError` is raised after the request status and audit insert in one transaction; the handler rolls back and the demonstration asserts that both request state and update count match their pre-transaction values.

The demo uses a local SQLite file and synthetic records only. Do not treat the sample contact numbers or sample data as real service records. For a production deployment, protect the database file with operating-system permissions and add authentication/authorization at the application boundary.
