from pymongo import MongoClient
import json

client = MongoClient("mongodb://127.0.0.1:27017")
db = client["ridesync_db"]


def find_values(obj, key):
    """Recursively find all values for a key in a MongoDB explain result."""
    results = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                results.append(v)
            results.extend(find_values(v, key))

    elif isinstance(obj, list):
        for item in obj:
            results.extend(find_values(item, key))

    return results


# -----------------------------
# Workflow 3: GEO NEAR
# -----------------------------

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
            "query": {
                "isAvailable": True
            }
        }
    },
    {"$sort": {"dist_meters": 1}},
    {"$limit": 5},
    {
        "$project": {
            "_id": 0,
            "vehicleId": 1,
            "distance_km": {
                "$divide": ["$dist_meters", 1000]
            },
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


# MongoDB 8 places these values inside the $geoNearCursor stage,
# so search recursively instead of assuming a fixed structure.

geo_execution_times = find_values(
    geo_explain,
    "executionTimeMillisEstimate"
)

geo_nreturned = find_values(
    geo_explain,
    "nReturned"
)

geo_keys = find_values(
    geo_explain,
    "keysExamined"
)

geo_docs = find_values(
    geo_explain,
    "docsExamined"
)

geo_indexes = find_values(
    geo_explain,
    "indexName"
)


# Find the final nReturned from the pipeline.
geo_final_returned = None

if geo_nreturned:
    # Usually the final stage is the last nReturned value.
    geo_final_returned = geo_nreturned[-1]


# Find maximum keys/docs examined.
geo_total_keys = max(geo_keys) if geo_keys else None
geo_total_docs = max(geo_docs) if geo_docs else None


# Get useful index names.
geo_indexes = sorted(set(str(x) for x in geo_indexes))


# -----------------------------
# Workflow 4: FACET
# -----------------------------

facet_pipeline = [
    {"$unwind": "$feedback_tags"},
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

facet_times = find_values(
    facet_explain,
    "executionTimeMillisEstimate"
)

facet_nreturned = find_values(
    facet_explain,
    "nReturned"
)

facet_keys = find_values(
    facet_explain,
    "keysExamined"
)

facet_docs = find_values(
    facet_explain,
    "docsExamined"
)


facet_final_returned = (
    facet_nreturned[-1]
    if facet_nreturned
    else None
)

facet_total_keys = (
    max(facet_keys)
    if facet_keys
    else 0
)

facet_total_docs = (
    max(facet_docs)
    if facet_docs
    else 0
)


# -----------------------------
# Compact report
# -----------------------------

report = {
    "database": "ridesync_db",
    "mongo_version": db.client.server_info()["version"],

    "workflow3_geonear": {
        "collection": "TelemetryPings",
        "query": "Find 5 available vehicles within 5 km",
        "index_used": geo_indexes,
        "nReturned_final_stage": geo_final_returned,
        "max_keysExamined_observed": geo_total_keys,
        "max_docsExamined_observed": geo_total_docs,
        "executionTimeMillisEstimate_last": (
            geo_execution_times[-1]
            if geo_execution_times
            else None
        )
    },

    "workflow4_facet": {
        "collection": "TripReviews",
        "query": "Rating distribution, common feedback, average rating",
        "nReturned_final_stage": facet_final_returned,
        "max_keysExamined_observed": facet_total_keys,
        "max_docsExamined_observed": facet_total_docs,
        "executionTimeMillisEstimate_last": (
            facet_times[-1]
            if facet_times
            else None
        )
    }
}


with open(
    "performance/mongo_execution_stats.json",
    "w"
) as f:
    json.dump(report, f, indent=2)


print("======================================")
print("MongoDB Performance Summary")
print("======================================")
print(json.dumps(report, indent=2))
print()
print("Saved to:")
print("performance/mongo_execution_stats.json")


client.close()
