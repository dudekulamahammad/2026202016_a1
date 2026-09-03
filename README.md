# RideSync A1 — MongoDB Setup & Execution

Run all commands from the repository root.

---

## 1. Clone Repository

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

## 2. Start MongoDB

```bash
sudo systemctl start mongod
```

Check MongoDB:

```bash
mongosh --eval 'db.runCommand({ ping: 1 })'
```

---

## 3. Install PyMongo

```bash
python3 -m pip install pymongo
```

---

## 4. Generate MongoDB Data

```bash
python3 data_generations/mongo_seeder.py
```

Creates:

* `VehicleMetadata` — 150 documents
* `TripReviews` — 100,000 documents
* `TelemetryPings` — 500,000 documents

Verify:

```bash
mongosh --quiet --eval 'const db=db.getSiblingDB("ridesync_db"); print("VehicleMetadata:",db.VehicleMetadata.countDocuments()); print("TripReviews:",db.TripReviews.countDocuments()); print("TelemetryPings:",db.TelemetryPings.countDocuments());'
```

---

## 5. Create Indexes

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

## 6. Run Workflow 3 — $geoNear

```bash
mongosh --quiet --file mongo/02_workflow3_geonear.js
```

Runs the nearest available vehicle search within 5 km.

---

## 7. Run Workflow 4 — $facet

```bash
mongosh --quiet --file mongo/03_workflow4_facet.js
```

Runs:

* Rating distribution
* Top feedback tags
* Average rating

---

## 8. Generate EXPLAIN Statistics

```bash
python3 data_generations/generate_mongo_stats.py
```

Generates:

```text
performance/mongo_execution_stats.json
performance/mongo_explain_raw.json
```

View summary:

```bash
cat performance/mongo_execution_stats.json
```

---

## 9. Run Complete MongoDB Report

```bash
mongosh --quiet --file mongo/run_all_mongo_workflows.js
```

This is the **main MongoDB demo command**.

It shows:

* Database/collection counts
* Indexes
* Workflow 3 results
* Workflow 3 EXPLAIN statistics
* Workflow 4 rating distribution
* Top feedback tags
* Average rating
* Workflow 4 EXPLAIN statistics

---

## 10. View Performance Files

```bash
ls -lh performance/
```

View MongoDB execution summary:

```bash
cat performance/mongo_execution_stats.json
```

View raw EXPLAIN:

```bash
less performance/mongo_explain_raw.json
```

Press `q` to exit.

---

## 11. Remove Python Cache Before Git

```bash
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
```

```bash
find . -name "*.pyc" -delete
```

---

## 12. Check Git

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

If your branch is `main`:

```bash
git push origin main
```

---

# Quick Demo

If everything is already installed, run these from the repository root:

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

# Repository Structure

```text
docs/
mongo/
data_generations/
performance/
sql/
README.md
```

MongoDB scripts:

```text
mongo/
├── 01_collections_and_indexes.js
├── 02_workflow3_geonear.js
├── 03_workflow4_facet.js
└── run_all_mongo_workflows.js
```

Data generation:

```text
data_generations/
├── mongo_seeder.py
├── generate_mongo_stats.py
├── generate_trip_reviews.py
└── get_geo_summary.py
```

Performance evidence:

```text
performance/
├── mongo_execution_stats.json
├── mongo_explain_raw.json
├── workflow3_explain_executionStats.log
└── workflow4_explain_executionStats.log
```

**MongoDB data is generated locally. No database dump or raw data is stored in GitHub.**
