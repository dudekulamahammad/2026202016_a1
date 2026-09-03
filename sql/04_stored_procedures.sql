CREATE OR REPLACE PROCEDURE sp_book_ride(
    p_rider_id UUID,
    p_vehicle_id UUID,
    p_fare_amount NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_current_balance NUMERIC;
BEGIN
    -- 1. Lock rider row to prevent race conditions
    SELECT wallet_balance
    INTO v_current_balance
    FROM riders
    WHERE id = p_rider_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Rider with ID % not found', p_rider_id;
    END IF;

    -- 2. Check sufficient balance
    IF v_current_balance < p_fare_amount THEN
        RAISE EXCEPTION
            'Insufficient balance. Required: %, Available: %',
            p_fare_amount, v_current_balance;
    END IF;

    -- 3. Check vehicle is active
    IF NOT EXISTS (
        SELECT 1
        FROM vehicles
        WHERE id = p_vehicle_id
          AND is_active = TRUE
    ) THEN
        RAISE EXCEPTION 'Vehicle % is not available', p_vehicle_id;
    END IF;

    -- 4. Deduct fare
    UPDATE riders
    SET wallet_balance = wallet_balance - p_fare_amount
    WHERE id = p_rider_id;

    -- 5. Create trip
    INSERT INTO trips (
        rider_id,
        vehicle_id,
        fare_amount,
        status
    )
    VALUES (
        p_rider_id,
        p_vehicle_id,
        p_fare_amount,
        'REQUESTED'
    );

    RAISE NOTICE 'Ride booked successfully for Rider %', p_rider_id;
END;
$$;