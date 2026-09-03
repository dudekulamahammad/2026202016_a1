# RideSync A1 — Database Setup & Execution Guide

This repository contains the PostgreSQL and MongoDB implementation for the RideSync A1 assignment.

Run commands from the repository root.

---

# 1. Clone Repository

```bash
cd ~/Desktop/gitAsgn
git clone https://github.com/dudekulamahammad/2026202016_a1.git
cd 2026202016_a1
```

Check files:

```bash
find . -maxdepth 2 -type f | sort
```

---

# 2. PostgreSQL Setup

## 2.1 Create PostgreSQL Database

Create the database:

```bash
createdb ridesync_db
```

If the database already exists, continue to the next step.

---

## 2.2 Create Schema

Run the schema DDL:

```bash
psql -d ridesync_db -f sql/01_schema_ddl.sql
```

Creates the main RideSync tables, keys, and constraints.

---

## 2.3 Create Indexes

```bash
psql -d ridesync_db -f sql/02_indexes.sql
```

Creates partial and secondary indexes.

---

## 2.4 Create Triggers and Audit

```bash
psql -d ridesync_db -f sql/03_triggers_and_audit.sql
```

Creates wallet audit triggers.

---

## 2.5 Create Stored Procedures

```bash
psql -d ridesync_db -f sql/04_stored_procedures.sql
```

Creates the atomic ride-booking procedure.

---

## 2.6 Create Materialized Views

```bash
psql -d ridesync_db -f sql/05_materialized_views.sql
```

Creates vehicle statistics materialized views.

---

## 2.7 Run Window Analytics

```bash
psql -d ridesync_db -f sql/06_window_analytics.sql
```

Runs the Workflow 2 window-function analysis.

---

## 2.8 Generate PostgreSQL Data

Install the required Python package:

```bash
python3 -m pip install psycopg2-binary
```

Run the PostgreSQL seeder:

```bash
python3 data_generations/postgres_seeder.py
```

This generates the required mock PostgreSQL data.

---

# 3. MongoDB Setup

## 3.1 Start MongoDB

```bash
sudo systemctl start mongod
```

Check MongoDB:

```bash
mongosh --eval 'db.runCommand({ ping: 1 })'
```

---

## 3.2 Install PyMongo

```bash
python3 -m pip install pymongo
```

---

## 3.3 Generate MongoDB Data

```bash
python3 data_generations/mongo_seeder.py
```

Generates:

* `VehicleMetadata` — 150 documents
* `TripReviews` — 100,000 documents
* `TelemetryPings` — 500,000 documents

Verify counts:

```bash
mongosh --quiet --eval 'const db=db.getSiblingDB("ridesync_db"); print("VehicleMetadata:",db.VehicleMetadata.countDocuments()); print("TripReviews:",db.TripReviews.countDocuments()); print("TelemetryPings:",db.TelemetryPings.countDocuments());'
```

---

# 4. MongoDB Indexes

Create indexes:

```bash
mongosh --quiet --file mongo/01_collections_and_indexes.js
```

Creates:

* `location_2dsphere`
* `createdAt_1` TTL index
* `rating_1`
* `vehicleId_1`

Verify:

```bash
mongosh --quiet --eval 'const db=db.getSiblingDB("ridesync_db"); printjson(db.TelemetryPings.getIndexes()); printjson(db.TripReviews.getIndexes());'
```

---

# 5. MongoDB Workflow 3 — $geoNear

Run:

```bash
mongosh --quiet --file mongo/02_workflow3_geonear.js
```

Runs the nearest available vehicle search within 5 km using the `2dsphere` index.

---

# 6. MongoDB Workflow 4 — $facet

Run:

```bash
mongosh --quiet --file mongo/03_workflow4_facet.js
```

Runs:

* Rating distribution
* Top feedback tags
* Average rating

---

# 7. MongoDB EXPLAIN Statistics

Generate performance evidence:

```bash
python3 data_generations/generate_mongo_stats.py
```

Creates/updates:

```text
performance/mongo_execution_stats.json
performance/mongo_explain_raw.json
```

View the summary:

```bash
cat performance/mongo_execution_stats.json
```

View the raw explain output:

```bash
less performance/mongo_explain_raw.json
```

Press `q` to exit.

---

# 8. Complete MongoDB Report

Run:

```bash
mongosh --quiet --file mongo/run_all_mongo_workflows.js
```

This displays:

* Collection counts
* Indexes
* Workflow 3 results
* Workflow 3 execution statistics
* Workflow 4 rating distribution
* Top feedback tags
* Average rating
* Workflow 4 execution statistics

---

# 9. PostgreSQL Performance Evidence

The PostgreSQL execution plans are stored in:

```text
performance/postgres_explain_analyzes.txt
```

View them:

```bash
cat performance/postgres_explain_analyzes.txt
```

The file contains `EXPLAIN (ANALYZE, BUFFERS)` output for the PostgreSQL workflow.

---

# 10. MongoDB Performance Files

Check:

```bash
ls -lh performance/
```

MongoDB evidence files:

```text
mongo_execution_stats.json
mongo_explain_raw.json
workflow3_explain_executionStats.log
workflow4_explain_executionStats.log
```

---

# 11. Remove Python Cache Files

Before committing, remove Python cache files:

```bash
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
```

```bash
find . -name "*.pyc" -delete
```

Verify:

```bash
find . -name "__pycache__" -o -name "*.pyc"
```

There should be no output.

---

# 12. Repository Structure

```text
2026202016_a1/
│
├── README.md
│
├── docs/
│   ├── relational_erd.png
│   └── mongo_schema_map.json
│
├── sql/
│   ├── 01_schema_ddl.sql
│   ├── 02_indexes.sql
│   ├── 03_triggers_and_audit.sql
│   ├── 04_stored_procedures.sql
│   ├── 05_materialized_views.sql
│   └── 06_window_analytics.sql
│
├── mongo/
│   ├── 01_collections_and_indexes.js
│   ├── 02_workflow3_geonear.js
│   ├── 03_workflow4_facet.js
│   └── run_all_mongo_workflows.js
│
├── data_generations/
│   ├── postgres_seeder.py
│   ├── mongo_seeder.py
│   ├── generate_mongo_stats.py
│   ├── generate_trip_reviews.py
│   └── get_geo_summary.py
│
└── performance/
    ├── postgres_explain_analyzes.txt
    ├── mongo_execution_stats.json
    ├── mongo_explain_raw.json
    ├── workflow3_explain_executionStats.log
    └── workflow4_explain_executionStats.log
```

---

# 13. GitHub

Check repository status:

```bash
git status
```

Add files:

```bash
git add .
```

Commit:

```bash
git commit -m "Add RideSync database assignment implementation"
```

Push:

```bash
git push origin master
```

If the repository uses `main`:

```bash
git push origin main
```

---

# 14. Quick MongoDB Demo

From the repository root:

```bash
sudo systemctl start mongod
```

```bash
python3 data_generations/mongo_seeder.py
```

```bash
mongosh --quiet --file mongo/01_collections_and_indexes.js
```

```bash
mongosh --quiet --file mongo/run_all_mongo_workflows.js
```

```bash
python3 data_generations/generate_mongo_stats.py
```

```bash
cat performance/mongo_execution_stats.json
```

---

# 15. Quick PostgreSQL Demo

From the repository root:

```bash
createdb ridesync_db
```

```bash
psql -d ridesync_db -f sql/01_schema_ddl.sql
```

```bash
psql -d ridesync_db -f sql/02_indexes.sql
```

```bash
psql -d ridesync_db -f sql/03_triggers_and_audit.sql
```

```bash
psql -d ridesync_db -f sql/04_stored_procedures.sql
```

```bash
psql -d ridesync_db -f sql/05_materialized_views.sql
```

```bash
psql -d ridesync_db -f sql/06_window_analytics.sql
```

```bash
python3 data_generations/postgres_seeder.py
```

---

# 16. Important Submission Note

The database data itself is **not stored in GitHub**.

Only the following are submitted:

* SQL scripts
* MongoDB scripts
* Python data-generation scripts
* Schema diagrams/maps
* Performance/explain evidence
* README documentation

Do **not** commit:

* MongoDB database dumps
* PostgreSQL data dumps
* CSV exports
* `__pycache__`
* `.pyc` files
* Python virtual environments
* Raw database files
