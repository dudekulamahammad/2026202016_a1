-- =============================================================================
-- 02_INDEXES.SQL
-- Purpose: Performance optimization and conditional business logic enforcement.
-- =============================================================================

-- 1. PARTIAL UNIQUE INDEX (Business Logic Requirement)
-- Ensures a rider cannot have more than one "active" trip at a time.
-- This prevents a rider from booking a second ride while already REQUESTED or IN TRANSIT.
CREATE UNIQUE INDEX idx_unique_active_rider_trip 
ON trips (rider_id) 
WHERE status IN ('REQUESTED', 'IN TRANSIT');


-- 2. SECONDARY INDEXES FOR PERFORMANCE

-- Optimization for Foreign Key lookups (PostgreSQL does not index FKs by default)
CREATE INDEX idx_trips_rider_id ON trips(rider_id);
CREATE INDEX idx_trips_vehicle_id ON trips(vehicle_id);

-- Optimization for the 7-day moving average analytics (Workflow 2)
-- B-Tree index on created_at since we filter and group by time ranges.
CREATE INDEX idx_trips_created_at ON trips(created_at);

-- Optimization for Vehicle Revenue ranking
-- Helps in filtering trips by status (COMPLETED) when calculating earnings.
CREATE INDEX idx_trips_status_completed ON trips(status) WHERE status = 'COMPLETED';

-- Optimization for Vehicle Lookups
-- Searching for specific vehicles by license plate or active status.
CREATE INDEX idx_vehicles_license_plate ON vehicles(license_plate);
CREATE INDEX idx_vehicles_active_status ON vehicles(is_active);

-- Optimization for Rider Lookups
CREATE INDEX idx_riders_name ON riders(name);