CREATE TABLE users (
    user_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(10) NOT NULL DEFAULT 'user'
        CHECK (role IN ('user', 'admin')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE venues (
    venue_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    venue_name VARCHAR(150) NOT NULL,
    location VARCHAR(255)
);

CREATE TABLE events (
    event_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    venue_id INTEGER NOT NULL REFERENCES venues(venue_id),
    event_name VARCHAR(150) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    ticket_price NUMERIC(10, 2) NOT NULL
        CHECK (ticket_price >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled'
        CHECK (status IN ('scheduled', 'cancelled'))
);

CREATE TABLE seats (
    seat_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    venue_id INTEGER NOT NULL REFERENCES venues(venue_id),
    seat_label VARCHAR(10) NOT NULL,
    seat_type VARCHAR(30) NOT NULL DEFAULT 'Standard',
    UNIQUE (venue_id, seat_label)
);

CREATE TABLE bookings (
    booking_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    event_id INTEGER NOT NULL REFERENCES events(event_id),
    booking_reference VARCHAR(30) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'confirmed'
        CHECK (status IN ('confirmed', 'cancelled')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE booking_seats (
    booking_seat_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    booking_id INTEGER NOT NULL
        REFERENCES bookings(booking_id),
    event_id INTEGER NOT NULL REFERENCES events(event_id),
    seat_id INTEGER NOT NULL REFERENCES seats(seat_id),
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    UNIQUE (event_id, seat_id)
);

CREATE TABLE seat_holds (
    hold_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(event_id),
    seat_id INTEGER NOT NULL REFERENCES seats(seat_id),
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    expires_at TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'released', 'expired')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);