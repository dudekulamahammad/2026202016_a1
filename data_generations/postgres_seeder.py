import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import psycopg2
from psycopg2.extras import register_uuid, execute_values, execute_batch


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "ridesync_v2",
    "user": "postgres",
    "password": os.getenv("PGPASSWORD"),
}


# ============================================================
# DATASET SIZE
# ============================================================

NUM_RIDERS = 1000
NUM_VEHICLES = 100
NUM_TRIPS = 100_000
NUM_WALLET_TRANSACTIONS = 100_000

BATCH_SIZE = 5_000


# ============================================================
# VEHICLE CLASSES
# ============================================================

VEHICLE_CLASSES = [
    "Sedan",
    "SUV",
    "Hatchback",
]


# ============================================================
# CONNECTION
# ============================================================

def get_connection():

    password = DB_CONFIG["password"]

    if not password:
        import getpass
        password = getpass.getpass("Enter PostgreSQL password: ")
        DB_CONFIG["password"] = password

    conn = psycopg2.connect(**DB_CONFIG)

    # Tell psycopg2 how to handle Python UUID objects
    register_uuid(conn_or_curs=conn)

    return conn


# ============================================================
# CLEAR EXISTING DATA
# ============================================================

def clear_existing_data(conn):

    """
    Clears previously seeded data.

    Tables are cleared in dependency order.
    """

    with conn.cursor() as cur:

        cur.execute("DELETE FROM trips;")

        cur.execute("DELETE FROM wallet_audit_logs;")

        cur.execute("DELETE FROM riders;")

        cur.execute("DELETE FROM vehicles;")

    conn.commit()

    print("Existing RideSync data cleared.")


# ============================================================
# INSERT RIDERS
# ============================================================

def insert_riders(conn):

    riders = []

    print(f"Generating {NUM_RIDERS:,} riders...")

    rows = []

    for i in range(NUM_RIDERS):

        rider_id = uuid.uuid4()

        name = f"Rider_{i + 1:04d}"

        # Large enough starting balance to safely support
        # many wallet transactions.
        balance = Decimal(random.randint(8000, 12000))

        rows.append(
            (
                rider_id,
                name,
                balance,
            )
        )

        riders.append(
            {
                "id": rider_id,
                "name": name,
                "initial_balance": balance,
                "balance": balance,
            }
        )

    with conn.cursor() as cur:

        execute_values(
            cur,
            """
            INSERT INTO riders (
                id,
                name,
                wallet_balance
            )
            VALUES %s
            """,
            rows,
        )

    conn.commit()

    print(f"Inserted {len(riders):,} riders.")

    return riders


# ============================================================
# INSERT VEHICLES
# ============================================================

def insert_vehicles(conn):

    vehicles = []

    print(f"Generating {NUM_VEHICLES:,} vehicles...")

    rows = []

    for i in range(NUM_VEHICLES):

        vehicle_id = uuid.uuid4()

        # Example:
        # MH01AB0001
        # MH02AB0002
        # ...
        license_plate = f"MH{(i % 99) + 1:02d}AB{i + 1:04d}"

        vehicle_class = random.choice(VEHICLE_CLASSES)

        rows.append(
            (
                vehicle_id,
                license_plate,
                vehicle_class,
                True,
            )
        )

        vehicles.append(
            {
                "id": vehicle_id,
                "license_plate": license_plate,
                "class": vehicle_class,
            }
        )

    with conn.cursor() as cur:

        execute_values(
            cur,
            """
            INSERT INTO vehicles (
                id,
                license_plate,
                class,
                is_active
            )
            VALUES %s
            """,
            rows,
        )

    conn.commit()

    print(f"Inserted {len(vehicles):,} vehicles.")

    return vehicles


# ============================================================
# INSERT COMPLETED TRIPS
# ============================================================

def insert_completed_trips(conn, riders, vehicles):

    """
    Generates exactly 100,000 completed trips
    distributed across the last 14 days.

    Batch insertion is used for better performance.
    """

    print(f"Generating {NUM_TRIPS:,} completed trips...")

    now = datetime.now(timezone.utc)

    trips = []

    inserted = 0

    with conn.cursor() as cur:

        for i in range(NUM_TRIPS):

            rider = random.choice(riders)

            vehicle = random.choice(vehicles)

            # Random day in the last 14 days
            days_ago = random.randint(0, 13)

            day_start = (
                now - timedelta(days=days_ago)
            ).replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            # Random time between 7 AM and 10 PM
            created_at = day_start + timedelta(
                seconds=random.randint(
                    7 * 60 * 60,
                    22 * 60 * 60,
                )
            )

            # Don't allow future timestamps
            if created_at > now:
                created_at = now

            fare = Decimal(
                random.randint(100, 800)
            ).quantize(
                Decimal("0.01")
            )

            trips.append(
                (
                    uuid.uuid4(),
                    rider["id"],
                    vehicle["id"],
                    fare,
                    "COMPLETED",
                    created_at,
                )
            )

            if len(trips) >= BATCH_SIZE:

                execute_values(
                    cur,
                    """
                    INSERT INTO trips (
                        id,
                        rider_id,
                        vehicle_id,
                        fare_amount,
                        status,
                        created_at
                    )
                    VALUES %s
                    """,
                    trips,
                )

                inserted += len(trips)

                conn.commit()

                print(
                    f"Inserted {inserted:,} / "
                    f"{NUM_TRIPS:,} trips"
                )

                trips.clear()

        # Remaining trips
        if trips:

            execute_values(
                cur,
                """
                INSERT INTO trips (
                    id,
                    rider_id,
                    vehicle_id,
                    fare_amount,
                    status,
                    created_at
                )
                VALUES %s
                """,
                trips,
            )

            inserted += len(trips)

            conn.commit()

    print(
        f"Inserted exactly {inserted:,} completed trips."
    )

    return inserted


# ============================================================
# CREATE 100K+ WALLET / AUDIT TRANSACTIONS
# ============================================================

def create_wallet_activity(conn, riders):

    """
    Generate 100,000 wallet transactions.

    IMPORTANT:
    We DO NOT insert directly into wallet_audit_logs.

    Every UPDATE to riders.wallet_balance fires
    trg_wallet_audit, which automatically creates
    the corresponding wallet_audit_logs row.
    """

    print(
        f"Generating {NUM_WALLET_TRANSACTIONS:,} "
        "wallet transactions..."
    )

    operations = []

    topups = 0
    deductions = 0

    # Keep a Python-side copy of balances so that
    # deductions never exceed the available balance.
    balances = {
        rider["id"]: rider["balance"]
        for rider in riders
    }

    for i in range(NUM_WALLET_TRANSACTIONS):

        rider = random.choice(riders)

        rider_id = rider["id"]

        current_balance = balances[rider_id]

        # Roughly 55% top-ups, 45% deductions.
        # This keeps balances safely positive while
        # producing a realistic mixture of transactions.
        if random.random() < 0.55:

            amount = Decimal(
                random.randint(100, 1500)
            )

            operations.append(
                (
                    amount,
                    rider_id,
                )
            )

            balances[rider_id] += amount

            topups += 1

        else:

            # Make sure deduction is affordable.
            max_deduction = min(
                1000,
                int(current_balance)
            )

            if max_deduction < 100:

                # If balance is low, perform a top-up instead.
                amount = Decimal(
                    random.randint(100, 1500)
                )

                operations.append(
                    (
                        amount,
                        rider_id,
                    )
                )

                balances[rider_id] += amount

                topups += 1

            else:

                amount = Decimal(
                    random.randint(
                        100,
                        max_deduction,
                    )
                )

                operations.append(
                    (
                        -amount,
                        rider_id,
                    )
                )

                balances[rider_id] -= amount

                deductions += 1

    print(
        f"Prepared {len(operations):,} wallet transactions."
    )

    print(
        f"  Top-ups:      {topups:,}"
    )

    print(
        f"  Deductions:   {deductions:,}"
    )

    print(
        "Applying transactions through riders.wallet_balance..."
    )

    processed = 0

    with conn.cursor() as cur:

        for start in range(
            0,
            len(operations),
            BATCH_SIZE
        ):

            batch = operations[
                start:start + BATCH_SIZE
            ]

            # Each UPDATE fires the wallet audit trigger.
            execute_batch(
                cur,
                """
                UPDATE riders
                SET wallet_balance =
                    wallet_balance + %s
                WHERE id = %s;
                """,
                batch,
                page_size=BATCH_SIZE,
            )

            conn.commit()

            processed += len(batch)

            print(
                f"Processed {processed:,} / "
                f"{NUM_WALLET_TRANSACTIONS:,} "
                "wallet transactions"
            )

    print(
        "\nWallet transactions completed."
    )

    print(
        "wallet_audit_logs were generated automatically "
        "by trg_wallet_audit."
    )

    return topups, deductions


# ============================================================
# VERIFY DATA
# ============================================================

def verify_data(conn):

    with conn.cursor() as cur:

        cur.execute(
            "SELECT COUNT(*) FROM riders;"
        )

        rider_count = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM vehicles;"
        )

        vehicle_count = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM trips;"
        )

        trip_count = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM wallet_audit_logs;"
        )

        audit_count = cur.fetchone()[0]

    print("\n========================================")
    print("        RIDESYNC DATABASE STATUS")
    print("========================================")

    print(
        f"Riders:             {rider_count:,}"
    )

    print(
        f"Vehicles:           {vehicle_count:,}"
    )

    print(
        f"Trips:              {trip_count:,}"
    )

    print(
        f"Wallet audit logs:  {audit_count:,}"
    )

    print("========================================")

    if audit_count >= 100_000:

        print(
            "SUCCESS: 100k+ audit/ledger rows generated."
        )

    else:

        print(
            "WARNING: Audit row requirement not satisfied."
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "Connecting to RideSync PostgreSQL database..."
    )

    conn = None

    try:

        conn = get_connection()

        print("Connected successfully.\n")

        # 1. Clear old data
        clear_existing_data(conn)

        # 2. Create riders
        riders = insert_riders(conn)

        # 3. Create vehicles
        vehicles = insert_vehicles(conn)

        # 4. Create 100k trips
        insert_completed_trips(
            conn,
            riders,
            vehicles,
        )

        # 5. Create 100k wallet transactions
        #    -> trigger creates 100k audit rows
        create_wallet_activity(
            conn,
            riders,
        )

        # 6. Verify everything
        verify_data(conn)

        print(
            "\nSeeding completed successfully!"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print("\nERROR:")
        print(e)

    finally:

        if conn:
            conn.close()


if __name__ == "__main__":
    main()
