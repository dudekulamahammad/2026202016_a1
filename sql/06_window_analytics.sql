-- =============================================================================
-- 06_WINDOW_ANALYTICS.SQL
-- Purpose: Trend analysis and performance ranking using Window Functions.
-- =============================================================================

WITH daily_revenue AS (
    -- Aggregate daily revenue per vehicle
    SELECT 
        vehicle_id,
        date_trunc('day', created_at) AS trip_date,
        SUM(fare_amount) AS daily_fare
    FROM trips
    WHERE status = 'COMPLETED'
    GROUP BY vehicle_id, date_trunc('day', created_at)
),
moving_metrics AS (
    -- Calculate 7-day moving average of fare revenue per vehicle
    SELECT 
        vehicle_id,
        trip_date,
        daily_fare,
        AVG(daily_fare) OVER (
            PARTITION BY vehicle_id 
            ORDER BY trip_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS seven_day_moving_avg
    FROM daily_revenue
)
-- Final Ranking using DENSE_RANK
SELECT 
    v.license_plate,
    m.trip_date,
    m.daily_fare,
    ROUND(m.seven_day_moving_avg, 2) AS moving_avg,
    DENSE_RANK() OVER (
        PARTITION BY m.trip_date 
        ORDER BY m.seven_day_moving_avg DESC
    ) AS vehicle_rank_that_day
FROM moving_metrics m
JOIN vehicles v ON m.vehicle_id = v.id
ORDER BY m.trip_date DESC, vehicle_rank_that_day ASC;