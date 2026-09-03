// Workflow: Find nearest available vehicles within 5km of a rider in Downtown
// Coordinates: [longitude, latitude]
const riderLocation = [-73.9857, 40.7484]; // Example: Empire State Building

db.TelemetryPings.aggregate([
  {
    $geoNear: {
      near: { type: "Point", coordinates: riderLocation },
      distanceField: "dist_meters",
      maxDistance: 5000, // 5km
      spherical: true,
      query: { isAvailable: true } // Only pinging vehicles that aren't currently in a trip
    }
  },
  {
    $sort: { dist_meters: 1 }
  },
  {
    $limit: 5 // Return top 5 closest vehicles
  },
  {
    $project: {
      _id: 0,
      vehicleId: 1,
      distance_km: { $divide: ["$dist_meters", 1000] },
      location: 1
    }
  }
]);