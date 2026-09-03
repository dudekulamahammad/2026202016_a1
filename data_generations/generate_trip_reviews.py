from pymongo import MongoClient
from random import randint, choice
from datetime import datetime, timedelta
import random

client = MongoClient("mongodb://127.0.0.1:27017")
db = client["ridesync_db"]
collection = db["TripReviews"]

TARGET = 100_000
current = collection.count_documents({})
remaining = TARGET - current

print(f"Existing reviews: {current}")
print(f"Reviews to generate: {remaining}")

if remaining <= 0:
    print("TripReviews already has 100,000+ documents.")
    client.close()
    raise SystemExit

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
batch_size = 5000

for i in range(remaining):

    rating = choice(ratings)

    number_of_tags = randint(1, 4)
    review_tags = random.sample(tags, number_of_tags)

    created_at = datetime.utcnow() - timedelta(
        minutes=randint(0, 60 * 24 * 180)
    )

    batch.append({
        "vehicleId": f"V{randint(1, 5000):05d}",
        "rating": rating,
        "feedback_tags": review_tags,
        "driver_feedback": choice(feedback),
        "createdAt": created_at
    })

    if len(batch) >= batch_size:
        collection.insert_many(batch)
        print(f"Inserted {i + 1:,} / {remaining:,}")
        batch.clear()

if batch:
    collection.insert_many(batch)

final_count = collection.count_documents({})

print()
print("======================================")
print("TripReviews generation complete")
print("======================================")
print(f"Final TripReviews count: {final_count:,}")

client.close()
