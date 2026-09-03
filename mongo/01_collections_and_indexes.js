// Switch to the RideSync database
// use ridesync_db;

// --- 1. VehicleMetadata ---
// Stores flexible data like insurance details, maintenance logs, and car features.
db.createCollection("VehicleMetadata");

// --- 2. TripReviews ---
// Stores rider feedback.
db.createCollection("TripReviews");

// --- 3. TelemetryPings ---
// High-volume collection for real-time location tracking.
db.createCollection("TelemetryPings");

// --- INDEXES ---

// A. Geospatial Index: Mandatory for $geoNear queries
db.TelemetryPings.createIndex({ location: "2dsphere" });

// B. TTL Index: Automatically expires data after 2 hours (7200 seconds)
// This keeps the collection lean by purging old location pings.
db.TelemetryPings.createIndex({ "createdAt": 1 }, { expireAfterSeconds: 7200 });

// C. Review Analytics Indexes
db.TripReviews.createIndex({ rating: 1 });
db.TripReviews.createIndex({ vehicleId: 1 });
