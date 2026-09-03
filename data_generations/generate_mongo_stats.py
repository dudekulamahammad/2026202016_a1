from pymongo import MongoClient
from datetime import datetime
import json

client = MongoClient("mongodb://127.0.0.1:27017")
db = client["ridesync_db"]

# ============================================================
# WORKFLOW 3 — $geoNear
# ============================================================

geo_pipeline = [
    {
        "$geoNear": {
            "near": {
                "type": "Point",
                "coordinates": [-73.9857, 40.7484]
            },
            "distanceField": "dist_meters",
            "maxDistance": 5000,
            "spherical": True,
            "query": {"isAvailable": True}
        }
    },
    {"$sort": {"dist_meters": 1}},
    {"$limit": 5},
    {
        "$project": {
            "_id": 0,
            "vehicleId": 1,
            "distance_km": {"$divide": ["$dist_meters", 1000]},
            "location": 1
        }
    }
]

geo_explain = db.command(
    "explain",
    {
        "aggregate": "TelemetryPings",
        "pipeline": geo_pipeline,
        "cursor": {}
    },
    verbosity="executionStats"
)

# ============================================================
# WORKFLOW 4 — $facet
# ============================================================

facet_pipeline = [
    {
        "$facet": {
            "rating_distribution": [
                {
                    "$group": {
                        "_id": "$rating",
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id": -1}}
            ],

            "common_feedback": [
                {"$unwind": "$feedback_tags"},
                {
                    "$group": {
                        "_id": "$feedback_tags",
                        "total_occurrences": {"$sum": 1}
                    }
                },
                {"$sort": {"total_occurrences": -1}},
                {"$limit": 10}
            ],

            "overall_average_rating": [
                {
                    "$group": {
                        "_id": None,
                        "average_rating": {"$avg": "$rating"}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "average_rating": 1
                    }
                }
            ]
        }
    }
]

facet_explain = db.command(
    "explain",
    {
        "aggregate": "TripReviews",
        "pipeline": facet_pipeline,
        "cursor": {}
    },
    verbosity="executionStats"
)

# ============================================================
# Save RAW explain evidence
# ============================================================

raw = {
    "generated_at": datetime.now().isoformat(),
    "workflow3_geonear": geo_explain,
    "workflow4_facet": facet_explain
}

with open("performance/mongo_explain_raw.json", "w") as f:
    json.dump(raw, f, indent=2, default=str)

# ============================================================
# Extract useful statistics from MongoDB 8 explain output
# ============================================================

def collect_stage_stats(obj, stats):
    if isinstance(obj, dict):
        for key, value in obj.items():

            if key == "indexName" and isinstance(value, str):
                stats["indexes"].add(value)

            if key == "keysExamined" and isinstance(value, int):
                stats["keys_examined"].append(value)

            if key == "docsExamined" and isinstance(value, int):
                stats["docs_examined"].append(value)

            if key == "nReturned" and isinstance(value, (int, float)):
                stats["nReturned"].append(value)

            if key == "executionTimeMillisEstimate" and isinstance(value, (int, float)):
                stats["execution_times"].append(value)

            collect_stage_stats(value, stats)

    elif isinstance(obj, list):
        for item in obj:
            collect_stage_stats(item, stats)


def summarize(explain):
    stats = {
        "indexes": set(),
        "keys_examined": [],
        "docs_examined": [],
        "nReturned": [],
        "execution_times": []
    }

    collect_stage_stats(explain, stats)

    return {
        "indexes_observed": sorted(stats["indexes"]),
        "max_keysExamined_observed": max(stats["keys_examined"], default=0),
        "max_docsExamined_observed": max(stats["docs_examined"], default=0),
        "final_stage_nReturned": (
            stats["nReturned"][-1] if stats["nReturned"] else None
        ),
        "last_executionTimeMillisEstimate": (
            stats["execution_times"][-1]
            if stats["execution_times"]
            else None
        )
    }


geo_summary = summarize(geo_explain)
facet_summary = summarize(facet_explain)

# ============================================================
# Compact performance report
# ============================================================

report = {
    "database": "ridesync_db",
    "mongo_version": db.client.server_info()["version"],
    "generated_at": datetime.now().isoformat(),

    "workflow3_geonear": {
        "collection": "TelemetryPings",
        "operator": "$geoNear",
        "description": "Find 5 available vehicles within 5 km",
        "max_distance_meters": 5000,
        "filter": {
            "isAvailable": True
        },
        "index_used": geo_summary["indexes_observed"],
        "nReturned_final_stage": geo_summary["final_stage_nReturned"],
        "max_keysExamined_observed": geo_summary["max_keysExamined_observed"],
        "max_docsExamined_observed": geo_summary["max_docsExamined_observed"],
        "executionTimeMillisEstimate_last": geo_summary[
            "last_executionTimeMillisEstimate"
        ]
    },

    "workflow4_facet": {
        "collection": "TripReviews",
        "operators": [
            "$facet",
            "$unwind"
        ],
        "description": "Rating distribution, common feedback tags, overall average rating",
        "nReturned_final_stage": facet_summary["final_stage_nReturned"],
        "max_keysExamined_observed": facet_summary["max_keysExamined_observed"],
        "max_docsExamined_observed": facet_summary["max_docsExamined_observed"],
        "executionTimeMillisEstimate_last": facet_summary[
            "last_executionTimeMillisEstimate"
        ]
    }
}

with open("performance/mongo_execution_stats.json", "w") as f:
    json.dump(report, f, indent=2)

print("======================================")
print("MongoDB Execution Statistics")
print("======================================")

print("\nWorkflow 3 — $geoNear")
print("Index:", geo_summary["indexes_observed"])
print("Returned:", geo_summary["final_stage_nReturned"])
print(
    "Execution estimate:",
    geo_summary["last_executionTimeMillisEstimate"],
    "ms"
)
print(
    "Max keys examined:",
    geo_summary["max_keysExamined_observed"]
)
print(
    "Max documents examined:",
    geo_summary["max_docsExamined_observed"]
)

print("\nWorkflow 4 — $facet")
print("Returned:", facet_summary["final_stage_nReturned"])
print(
    "Execution estimate:",
    facet_summary["last_executionTimeMillisEstimate"],
    "ms"
)
print(
    "Max keys examined:",
    facet_summary["max_keysExamined_observed"]
)
print(
    "Max documents examined:",
    facet_summary["max_docsExamined_observed"]
)

print("\nSaved:")
print("performance/mongo_execution_stats.json")
print("performance/mongo_explain_raw.json")

client.close()
