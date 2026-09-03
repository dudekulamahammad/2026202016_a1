
-- 1. AUDIT TRIGGER FUNCTION
CREATE OR REPLACE FUNCTION fn_audit_wallet_change()
RETURNS TRIGGER AS $$
DECLARE
    v_amount_changed NUMERIC(12, 2);
    v_action_type VARCHAR(20);
BEGIN
    -- Calculate the difference
    v_amount_changed := NEW.wallet_balance - OLD.wallet_balance;

    -- Determine the action type based on the change
    IF v_amount_changed > 0 THEN
        v_action_type := 'TOP_UP';
    ELSIF v_amount_changed < 0 THEN
        v_action_type := 'FARE_DEDUCTION';
    ELSE
        -- If balance hasn't changed, do nothing
        RETURN NEW;
    END IF;

    -- Insert record into audit logs
    INSERT INTO wallet_audit_logs (
        rider_id,
        amount_changed,
        action_type,
        balance_after,
        timestamp
    )
    VALUES (
        NEW.id,
        v_amount_changed,
        v_action_type,
        NEW.wallet_balance,
        CURRENT_TIMESTAMP
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. BIND TRIGGER TO RIDERS TABLE
-- Fires AFTER an update specifically on the wallet_balance column
CREATE TRIGGER trg_wallet_audit
AFTER UPDATE OF wallet_balance ON riders
FOR EACH ROW
WHEN (OLD.wallet_balance IS DISTINCT FROM NEW.wallet_balance)
EXECUTE FUNCTION fn_audit_wallet_change();
