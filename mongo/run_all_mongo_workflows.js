// ============================================================
// RideSync - MongoDB Complete Workflow Runner
// ============================================================

const dbName = "ridesync_db";
const db = db.getSiblingDB(dbName);

print("============================================================");
print("              RIDESYNC MONGODB EXECUTION REPORT");
print("============================================================");
print("Database: " + dbName);
print("");

// ------------------------------------------------------------
// DATABASE SUMMARY
// ------------------------------------------------------------

print("DATABASE SUMMARY");
print("------------------------------------------------------------");

const collections = [
  "VehicleMetadata",
  "TripReviews",
  "TelemetryPings"
];

collections.forEach(function(name) {
  print(name + " : " + db.getCollection(name).countDocuments() + " documents");
});

print("");

// ------------------------------------------------------------
// INDEX SUMMARY
// ------------------------------------------------------------

print("INDEX SUMMARY");
print("------------------------------------------------------------");

collections.forEach(function(name) {
  print("");
  print(name + ":");

  db.getCollection(name).getIndexes().forEach(function(index) {
    let details = "  - " + index.name;

    if (index.expireAfterSeconds !== undefined) {
      details += " (TTL: " + index.expireAfterSeconds + " seconds)";
    }

    print(details);
  });
});

print("");

// ============================================================
// WORKFLOW 3
// NEAREST AVAILABLE VEHICLE
// ============================================================

print("============================================================");
print("WORKFLOW 3: NEAREST AVAILABLE VEHICLE");
print("============================================================");

const riderLocation = [-73.9857, 40.7484];

print("Search radius : 5 km");
print("Location      : [" + riderLocation[0] + ", " + riderLocation[1] + "]");
print("Filter        : isAvailable = true");
print("Index         : location_2dsphere");
print("");

const workflow3Pipeline = [
  {
    $geoNear: {
      near: {
        type: "Point",
        coordinates: riderLocation
      },
      distanceField: "dist_meters",
      maxDistance: 5000,
      spherical: true,
      query: {
        isAvailable: true
      }
    }
  },
  {
    $limit: 5
  },
  {
    $project: {
      _id: 0,
      vehicleId: 1,
      isAvailable: 1,
      location: 1,
      distance_km: {
        $round: [
          { $divide: ["$dist_meters", 1000] },
          3
        ]
      }
    }
  }
];

print("RESULTS");
print("------------------------------------------------------------");

const workflow3Results =
  db.TelemetryPings.aggregate(workflow3Pipeline).toArray();

workflow3Results.forEach(function(vehicle, index) {
  print(
    (index + 1) +
    ". " +
    vehicle.vehicleId +
    " | " +
    vehicle.distance_km +
    " km | available=" +
    vehicle.isAvailable
  );
});

print("");

print("WORKFLOW 3 EXPLAIN");
print("------------------------------------------------------------");

const workflow3Explain =
  db.TelemetryPings.explain("executionStats").aggregate(
    workflow3Pipeline
  );

const stats3 = workflow3Explain.stages[0].$geoNearCursor.executionStats;

print("Returned             : " + stats3.nReturned);
print("Execution time       : " + stats3.executionTimeMillis + " ms");
print("Keys examined        : " + stats3.totalKeysExamined);
print("Documents examined   : " + stats3.totalDocsExamined);

print("");


// ============================================================
// WORKFLOW 4
// MULTI-FACETED REVIEW ANALYTICS
// ============================================================

print("============================================================");
print("WORKFLOW 4: MULTI-FACETED REVIEW ANALYTICS");
print("============================================================");

print("Collection: TripReviews");
print("Documents : " + db.TripReviews.countDocuments());
print("Operators  : $facet, $unwind, $group, $sort, $avg");
print("");

const workflow4Pipeline = [
  {
    $facet: {

      // 1. Rating distribution
      rating_distribution: [
        {
          $group: {
            _id: "$rating",
            count: { $sum: 1 }
          }
        },
        {
          $sort: {
            _id: -1
          }
        }
      ],

      // 2. Most frequent feedback tags
      common_feedback: [
        {
          $unwind: "$feedback_tags"
        },
        {
          $group: {
            _id: "$feedback_tags",
            total_occurrences: { $sum: 1 }
          }
        },
        {
          $sort: {
            total_occurrences: -1
          }
        },
        {
          $limit: 10
        }
      ],

      // 3. Overall average rating
      overall_average_rating: [
        {
          $group: {
            _id: null,
            average_rating: { $avg: "$rating" }
          }
        },
        {
          $project: {
            _id: 0,
            average_rating: 1
          }
        }
      ]
    }
  }
];

const workflow4Results =
  db.TripReviews.aggregate(workflow4Pipeline).toArray()[0];

print("RATING DISTRIBUTION");
print("------------------------------------------------------------");

workflow4Results.rating_distribution.forEach(function(item) {
  print(item._id + " stars : " + item.count);
});

print("");

print("TOP 10 FEEDBACK TAGS");
print("------------------------------------------------------------");

workflow4Results.common_feedback.forEach(function(item, index) {
  print(
    (index + 1) +
    ". " +
    item._id +
    " : " +
    item.total_occurrences
  );
});

print("");

print("OVERALL AVERAGE RATING");
print("------------------------------------------------------------");

print(
  workflow4Results.overall_average_rating[0].average_rating
);

print("");


// ------------------------------------------------------------
// WORKFLOW 4 EXPLAIN
// ------------------------------------------------------------

print("WORKFLOW 4 EXPLAIN");
print("------------------------------------------------------------");

const workflow4Explain =
  db.TripReviews.explain("executionStats").aggregate(
    workflow4Pipeline
  );

const cursorStats =
  workflow4Explain.stages[0].$cursor.executionStats;

print("Returned             : " + cursorStats.nReturned);
print("Execution time       : " + cursorStats.executionTimeMillis + " ms");
print("Keys examined        : " + cursorStats.totalKeysExamined);
print("Documents examined   : " + cursorStats.totalDocsExamined);

print("");


// ============================================================
// FINAL SUMMARY
// ============================================================

print("============================================================");
print("FINAL MONGODB SUMMARY");
print("============================================================");

print("VehicleMetadata : " +
      db.VehicleMetadata.countDocuments());

print("TripReviews     : " +
      db.TripReviews.countDocuments());

print("TelemetryPings  : " +
      db.TelemetryPings.countDocuments());

print("");

print("Workflow 3 : $geoNear + 2dsphere geospatial index");
print("Workflow 4 : $facet + $unwind + $group + $sort + $avg");

print("");
print("============================================================");
print("                 END OF MONGODB REPORT");
print("============================================================");
