from pymongo import MongoClient
from datetime import datetime, timedelta
import random
import time


# ============================================================
# CONFIGURATION
# ============================================================

MONGO_URI = "mongodb://127.0.0.1:27017/"
DATABASE_NAME = "ridesync_db"

VEHICLE_COUNT = 150
REVIEW_COUNT = 100_000
TELEMETRY_COUNT = 500_000

BATCH_SIZE = 5_000

CENTER_LONGITUDE = -73.9857
CENTER_LATITUDE = 40.7484


# ============================================================
# CONNECT
# ============================================================

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

print("=" * 70)
print("RIDESYNC MONGODB DATA GENERATION")
print("=" * 70)
print(f"Database: {DATABASE_NAME}")
print()


# ============================================================
# COLLECTIONS
# ============================================================

vehicle_metadata = db["VehicleMetadata"]
trip_reviews = db["TripReviews"]
telemetry = db["TelemetryPings"]


# ============================================================
# VEHICLE METADATA
# ============================================================

print("-" * 70)
print("1. GENERATING VehicleMetadata")
print("-" * 70)

vehicle_metadata.delete_many({})

vehicle_classes = ["SEDAN", "SUV", "HATCHBACK", "VAN"]

feature_names = [
    "AC",
    "GPS",
    "Bluetooth",
    "WiFi",
    "ChildSeat",
    "WheelchairAccessible"
]

vehicle_docs = []

for i in range(1, VEHICLE_COUNT + 1):

    vehicle_id = f"V{i:05d}"

    selected_features = random.sample(
        feature_names,
        random.randint(2, 5)
    )

    vehicle_docs.append({
        "vehicleId": vehicle_id,
        "licensePlate": f"NYC-{i:03d}",
        "class": random.choice(vehicle_classes),

        "features": selected_features,

        "inspection": {
            "status": random.choice([
                "PASSED",
                "PASSED",
                "PASSED",
                "PENDING"
            ]),
            "date": datetime.utcnow() -
                    timedelta(days=random.randint(1, 180))
        },

        "maintenance": {
            "lastService": datetime.utcnow() -
                           timedelta(days=random.randint(1, 120)),
            "serviceDue": random.choice([False, False, False, True])
        },

        "insurance": {
            "provider": "RideSafe",
            "valid": random.choice([True, True, True, False])
        },

        "updatedAt": datetime.utcnow()
    })


vehicle_metadata.insert_many(vehicle_docs)

print(f"VehicleMetadata inserted: {len(vehicle_docs):,}")


# ============================================================
# TRIP REVIEWS
# ============================================================

print()
print("-" * 70)
print("2. GENERATING TripReviews")
print("-" * 70)

trip_reviews.delete_many({})

ratings = [1, 2, 3, 4, 5]

tags = [
    "clean",
    "friendly",
    "safe",
    "slow",
    "fast",
    "professional",
    "comfortable",
    "polite",
    "late",
    "helpful"
]

feedback = [
    "Good ride",
    "Excellent ride",
    "Driver was friendly",
    "Vehicle was clean",
    "Very comfortable",
    "Driver was professional",
    "Ride was safe",
    "Driver was late",
    "Overall good experience",
    "Could be faster"
]

batch = []
start_time = time.time()

for i in range(1, REVIEW_COUNT + 1):

    rating = random.choice(ratings)

    review_tags = random.sample(
        tags,
        random.randint(1, 4)
    )

    created_at = datetime.utcnow() - timedelta(
        minutes=random.randint(0, 60 * 24 * 180)
    )

    batch.append({
        "vehicleId": f"V{random.randint(1, VEHICLE_COUNT):05d}",
        "rating": rating,
        "feedback_tags": review_tags,
        "driver_feedback": random.choice(feedback),
        "createdAt": created_at
    })

    if len(batch) >= BATCH_SIZE:
        trip_reviews.insert_many(batch)
        batch.clear()

        if i % 25_000 == 0:
            print(f"Inserted reviews: {i:,}/{REVIEW_COUNT:,}")


if batch:
    trip_reviews.insert_many(batch)

elapsed = time.time() - start_time

print(f"TripReviews inserted: {trip_reviews.count_documents({}):,}")
print(f"Review generation time: {elapsed:.2f} seconds")


# ============================================================
# TELEMETRY PINGS
# ============================================================

print()
print("-" * 70)
print("3. GENERATING TelemetryPings")
print("-" * 70)

telemetry.delete_many({})

vehicle_ids = [
    f"V{i:05d}"
    for i in range(1, VEHICLE_COUNT + 1)
]

batch = []
start_time = time.time()

for i in range(1, TELEMETRY_COUNT + 1):

    vehicle_id = random.choice(vehicle_ids)

    longitude = (
        CENTER_LONGITUDE +
        random.uniform(-0.08, 0.08)
    )

    latitude = (
        CENTER_LATITUDE +
        random.uniform(-0.06, 0.06)
    )

    # Keep most pings recent so they survive the TTL index.
    if random.random() < 0.01:

        created_at = datetime.utcnow() - timedelta(
            hours=random.uniform(2.1, 5)
        )

    else:

        created_at = datetime.utcnow() - timedelta(
            minutes=random.uniform(0, 110)
        )

    batch.append({
        "vehicleId": vehicle_id,

        "isAvailable": random.choice([
            True,
            True,
            True,
            False
        ]),

        "location": {
            "type": "Point",
            "coordinates": [
                longitude,
                latitude
            ]
        },

        "createdAt": created_at
    })

    if len(batch) >= BATCH_SIZE:

        telemetry.insert_many(batch)
        batch.clear()

        if i % 50_000 == 0:
            print(
                f"Inserted telemetry: "
                f"{i:,}/{TELEMETRY_COUNT:,}"
            )


if batch:
    telemetry.insert_many(batch)

elapsed = time.time() - start_time

print(f"TelemetryPings inserted: {telemetry.count_documents({}):,}")
print(f"Telemetry generation time: {elapsed:.2f} seconds")


# ============================================================
# FINAL VERIFICATION
# ============================================================

print()
print("=" * 70)
print("MONGODB DATA GENERATION COMPLETE")
print("=" * 70)

print(
    f"VehicleMetadata : "
    f"{vehicle_metadata.count_documents({}):,}"
)

print(
    f"TripReviews     : "
    f"{trip_reviews.count_documents({}):,}"
)

print(
    f"TelemetryPings  : "
    f"{telemetry.count_documents({}):,}"
)

print()
print("Database:", DATABASE_NAME)
print("=" * 70)

client.close()
