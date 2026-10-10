
import streamlit as st
from db import get_events, get_event_seats, get_user_bookings
from booking import create_booking
from auth import login_user

st.set_page_config(
    page_title="SeatLock",
    page_icon="🎟️",
    layout="wide"
)

# Initialize session state
if "user" not in st.session_state:
    st.session_state["user"] = None

if "selected_seats" not in st.session_state:
    st.session_state["selected_seats"] = {}

# Application heading
st.title("🎟️ SeatLock")
st.caption("Smart Event Reservation System")

# --------------------------------
# LOGIN SCREEN
# --------------------------------
if st.session_state["user"] is None:
    st.subheader("Login to continue")

    with st.form("seatlock_login"):
        email = st.text_input("Email address")
        password = st.text_input(
            "Password",
            type="password"
        )
        submitted = st.form_submit_button("Login")

    if submitted:
        try:
            user = login_user(email, password)

            if user:
                st.session_state["user"] = user
                st.rerun()
            else:
                st.error("Invalid email or password.")

        except Exception as error:
            st.error("Unable to log in. Check your database connection.")
            st.code(str(error))

    st.info(
        "New to SeatLock? Register first by running "
        "`streamlit run test_auth.py` in another terminal."
    )
    st.stop()

# --------------------------------
# LOGGED-IN USER
# --------------------------------
user = st.session_state["user"]

st.write(f"Welcome, **{user['name']}**!")

if st.button("Logout"):
    st.session_state["user"] = None
    st.rerun()

st.divider()

# --------------------------------
# MY BOOKINGS
# --------------------------------
st.subheader("🎫 My Bookings")

try:
    my_bookings = get_user_bookings(user["user_id"])

    if not my_bookings:
        st.info("You haven't made any bookings yet.")

    else:
        for booking in my_bookings:
            (
                reference,
                booked_event_name,
                booked_venue_name,
                booked_start_time,
                booked_seats,
                total_price,
                booking_status,
                created_at
            ) = booking

            with st.expander(
                f"{booked_event_name} — {reference}"
            ):
                st.write(f"**Booking reference:** {reference}")
                st.write(f"**Event:** {booked_event_name}")
                st.write(f"**Venue:** {booked_venue_name}")
                st.write(f"**Event date:** {booked_start_time}")
                st.write(f"**Seats:** {booked_seats}")
                st.write(f"**Total price:** ₹{total_price:.2f}")
                st.write(f"**Status:** {booking_status.title()}")
                st.write(f"**Booked on:** {created_at}")

except Exception as error:
    st.error("Unable to load your bookings.")
    st.code(str(error))

st.divider()

# --------------------------------
# LOAD EVENTS
# --------------------------------
try:
    events = get_events()

    if not events:
        st.warning("No events are currently available.")
        st.stop()

    event_options = {
        f"{event[1]} — {event[2]}": event
        for event in events
    }

    selected_name = st.selectbox(
        "Choose an event",
        list(event_options.keys())
    )

    event = event_options[selected_name]

    event_id = int(event[0])
    event_name = event[1]
    venue_name = event[2]
    start_time = event[3]
    ticket_price = float(event[4])

    st.divider()

    left, middle, right = st.columns(3)

    left.metric("Selected Event", event_name)
    middle.metric("Ticket Price", f"₹{ticket_price:.2f}")
    right.write(f"**Venue**\n\n{venue_name}")

    st.write(f"**Event date and time:** {start_time}")

    # --------------------------------
    # SEAT SELECTION
    # --------------------------------
    selected = st.session_state["selected_seats"].setdefault(
        event_id, set()
    )

    seats = get_event_seats(event_id)

    if not seats:
        st.info("No seats are configured for this venue.")
        st.stop()

    st.subheader("🪑 Select Your Seats")

    st.markdown(
        "🟩 Available &nbsp;&nbsp; 🔵 Selected "
        "&nbsp;&nbsp; 🔴 Booked",
        unsafe_allow_html=True
    )

    st.info("🎬 SCREEN — FRONT OF THE AUDITORIUM")

    columns_per_row = 5

    for start in range(0, len(seats), columns_per_row):
        row_seats = seats[start:start + columns_per_row]
        cols = st.columns(columns_per_row)

        for col, seat in zip(cols, row_seats):
            seat_id = int(seat[0])
            seat_label = seat[1]
            is_booked = seat[3]

            with col:
                if is_booked:
                    # Remove seats that became booked
                    # from this session's selection.
                    selected.discard(seat_id)

                    st.button(
                        f"🔴 {seat_label}",
                        key=f"booked_{event_id}_{seat_id}",
                        disabled=True,
                        use_container_width=True
                    )

                else:
                    is_selected = seat_id in selected

                    button_label = (
                        f"🔵 {seat_label}"
                        if is_selected
                        else f"🟩 {seat_label}"
                    )

                    if st.button(
                        button_label,
                        key=f"seat_{event_id}_{seat_id}",
                        use_container_width=True
                    ):
                        if is_selected:
                            selected.remove(seat_id)
                        else:
                            selected.add(seat_id)

                        st.rerun()

    # --------------------------------
    # BOOKING SUMMARY
    # --------------------------------
    st.divider()
    st.subheader("🧾 Booking Summary")

    selected_seats = [
        seat
        for seat in seats
        if int(seat[0]) in selected and not seat[3]
    ]

    selected_labels = [
        seat[1] for seat in selected_seats
    ]

    selected_ids = [
        int(seat[0]) for seat in selected_seats
    ]

    total = len(selected_ids) * ticket_price

    st.write(
        "**Selected seats:**",
        ", ".join(selected_labels)
        if selected_labels
        else "None"
    )

    left, right = st.columns(2)

    left.metric("Number of Seats", len(selected_ids))
    right.metric("Total Price", f"₹{total:.2f}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Clear Selection",
            disabled=not selected
        ):
            selected.clear()
            st.rerun()

    with col2:
        if st.button(
            "Confirm Booking",
            type="primary",
            disabled=not selected_ids,
            use_container_width=True
        ):
            try:
                reference = create_booking(
                    user_id=user["user_id"],
                    event_id=event_id,
                    seat_ids=selected_ids
                )

                selected.clear()

                st.success("🎉 Booking successful!")
                st.write("**Your booking reference:**")
                st.code(reference)

                st.rerun()

            except Exception as error:
                st.error(f"Booking failed: {error}")
                st.info(
                    "Refresh the seat map and try again "
                    "if another user has booked those seats."
                )

except Exception as error:
    st.error("Unable to load SeatLock data.")
    st.code(str(error))