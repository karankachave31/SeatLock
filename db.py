import os
import streamlit as st
import psycopg


def get_connection():
    database_url = st.secrets.get(
        "DATABASE_URL",
        os.environ.get("DATABASE_URL")
    )

    if not database_url:
        raise ValueError("DATABASE_URL is missing.")

    return psycopg.connect(database_url)


def get_events():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    e.event_id,
                    e.event_name,
                    v.venue_name,
                    e.start_time,
                    e.ticket_price
                FROM events e
                JOIN venues v
                    ON e.venue_id = v.venue_id
                WHERE e.status = 'scheduled'
                ORDER BY e.start_time
            """)

            return cur.fetchall()


def get_event_seats(event_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    s.seat_id,
                    s.seat_label,
                    s.seat_type,
                    EXISTS (
                        SELECT 1
                        FROM booking_seats bs
                        JOIN bookings b
                          ON b.booking_id = bs.booking_id
                        WHERE bs.event_id = e.event_id
                          AND bs.seat_id = s.seat_id
                          AND b.status = 'confirmed'
                    ) AS is_booked
                FROM events e
                JOIN seats s
                  ON s.venue_id = e.venue_id
                WHERE e.event_id = %s
                ORDER BY s.seat_label
            """, (event_id,))

            return cur.fetchall()


def get_user_bookings(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    b.booking_reference,
                    e.event_name,
                    v.venue_name,
                    e.start_time,
                    STRING_AGG(s.seat_label, ', ' ORDER BY s.seat_label)
                        AS seats,
                    SUM(bs.price) AS total_price,
                    b.status,
                    b.created_at
                FROM bookings b
                JOIN events e
                    ON b.event_id = e.event_id
                JOIN venues v
                    ON e.venue_id = v.venue_id
                JOIN booking_seats bs
                    ON b.booking_id = bs.booking_id
                JOIN seats s
                    ON bs.seat_id = s.seat_id
                WHERE b.user_id = %s
                GROUP BY
                    b.booking_id,
                    b.booking_reference,
                    e.event_name,
                    v.venue_name,
                    e.start_time,
                    b.status,
                    b.created_at
                ORDER BY b.created_at DESC
            """, (user_id,))

            return cur.fetchall()


def get_user_bookings(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    b.booking_reference,
                    e.event_name,
                    v.venue_name,
                    e.start_time,
                    STRING_AGG(
                        s.seat_label,
                        ', ' ORDER BY s.seat_label
                    ) AS seats,
                    SUM(bs.price) AS total_price,
                    b.status,
                    b.created_at
                FROM bookings b
                JOIN events e
                    ON b.event_id = e.event_id
                JOIN venues v
                    ON e.venue_id = v.venue_id
                JOIN booking_seats bs
                    ON b.booking_id = bs.booking_id
                JOIN seats s
                    ON bs.seat_id = s.seat_id
                WHERE b.user_id = %s
                GROUP BY
                    b.booking_id,
                    b.booking_reference,
                    e.event_name,
                    v.venue_name,
                    e.start_time,
                    b.status,
                    b.created_at
                ORDER BY b.created_at DESC
            """, (user_id,))

            return cur.fetchall()
