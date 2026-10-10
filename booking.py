
import uuid

from db import get_connection


def create_booking(user_id, event_id, seat_ids):
    if not seat_ids:
        raise ValueError("Select at least one seat.")

    seat_ids = list(dict.fromkeys(int(s) for s in seat_ids))

    with get_connection() as conn:
        with conn.cursor() as cur:

            # Lock the event to serialize booking attempts
            cur.execute(
                """
                SELECT event_id, venue_id, ticket_price, status
                FROM events
                WHERE event_id = %s
                FOR UPDATE
                """,
                (event_id,)
            )

            event = cur.fetchone()

            if not event:
                raise ValueError("Event not found.")

            _, venue_id, price, status = event

            if status != "scheduled":
                raise ValueError("This event is not available.")

            # Verify the user exists
            cur.execute(
                "SELECT user_id FROM users WHERE user_id = %s",
                (user_id,)
            )

            if not cur.fetchone():
                raise ValueError("User not found.")

            # Lock and verify the requested seats
            cur.execute(
                """
                SELECT seat_id
                FROM seats
                WHERE venue_id = %s
                  AND seat_id = ANY(%s)
                ORDER BY seat_id
                FOR UPDATE
                """,
                (venue_id, seat_ids)
            )

            found_seats = {row[0] for row in cur.fetchall()}

            if found_seats != set(seat_ids):
                raise ValueError(
                    "Some selected seats don't belong to this venue."
                )

            # Reject seats that already have active allocations
            cur.execute(
                """
                SELECT seat_id
                FROM seat_allocations
                WHERE event_id = %s
                  AND seat_id = ANY(%s)
                """,
                (event_id, seat_ids)
            )

            if cur.fetchall():
                raise ValueError(
                    "One or more seats are already booked. Refresh and retry."
                )

            # Create booking
            reference = "SL-" + uuid.uuid4().hex[:10].upper()

            cur.execute(
                """
                INSERT INTO bookings
                    (user_id, event_id, booking_reference, status)
                VALUES (%s, %s, %s, 'confirmed')
                RETURNING booking_id
                """,
                (user_id, event_id, reference)
            )

            booking_id = cur.fetchone()[0]

            for seat_id in seat_ids:
                cur.execute(
                    """
                    INSERT INTO booking_seats
                        (booking_id, event_id, seat_id, price)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (booking_id, event_id, seat_id, price)
                )

                cur.execute(
                    """
                    INSERT INTO seat_allocations
                        (event_id, seat_id, booking_id)
                    VALUES (%s, %s, %s)
                    """,
                    (event_id, seat_id, booking_id)
                )

            return reference