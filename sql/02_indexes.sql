-- 1. PARTIAL UNIQUE INDEX (Business Logic Requirement)

CREATE UNIQUE INDEX idx_unique_active_rider_trip 
ON trips (rider_id) 
WHERE status IN ('REQUESTED', 'IN TRANSIT');


-- 2. SECONDARY INDEXES FOR PERFORMANCE

CREATE INDEX idx_trips_rider_id ON trips(rider_id);
CREATE INDEX idx_trips_vehicle_id ON trips(vehicle_id);


CREATE INDEX idx_trips_created_at ON trips(created_at);


CREATE INDEX idx_trips_status_completed ON trips(status) WHERE status = 'COMPLETED';


CREATE INDEX idx_vehicles_license_plate ON vehicles(license_plate);
CREATE INDEX idx_vehicles_active_status ON vehicles(is_active);


CREATE INDEX idx_riders_name ON riders(name);
