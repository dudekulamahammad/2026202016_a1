-- =============================================================================
-- 05_MATERIALIZED_VIEWS.SQL
-- Purpose: Faster read access for high-level vehicle statistics.
-- =============================================================================

-- 1. MATERIALIZED VIEW
CREATE MATERIALIZED VIEW mv_vehicle_stats AS
SELECT 
    v.id AS vehicle_id,
    v.license_plate,
    COUNT(t.id) AS total_trips,
    COALESCE(
        SUM(t.fare_amount) FILTER (WHERE t.status = 'COMPLETED'),
        0
    ) AS total_earnings
FROM vehicles v
LEFT JOIN trips t
    ON v.id = t.vehicle_id
GROUP BY
    v.id,
    v.license_plate;


-- 2. UNIQUE INDEX
-- Required to allow REFRESH MATERIALIZED VIEW CONCURRENTLY
CREATE UNIQUE INDEX idx_mv_vehicle_stats_id
ON mv_vehicle_stats (vehicle_id);


-- 3. REFRESH FUNCTION
CREATE OR REPLACE FUNCTION refresh_mv_vehicle_stats()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW mv_vehicle_stats;
END;
$$;


-- 4. REFRESH EXAMPLE
-- SELECT refresh_mv_vehicle_stats();