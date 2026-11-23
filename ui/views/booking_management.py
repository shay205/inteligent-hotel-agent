from datetime import date, timedelta

import pandas as pd
import streamlit as st

from hotel_agent.config import format_money
from hotel_agent.models.entities import Preferences
from hotel_agent.reporting.confirmation import build_confirmation_html, build_confirmation_text
from hotel_agent.services.booking_manager import BookingError
from hotel_agent.services.validators import ValidationError, validate_stay_dates
from ui.components import flash, hero, money_df, rerun, room_card, show_flash, show_table


def _apply_prefill(ctx) -> None:
    """Values sent from 'Book this room' are copied into the form widgets."""
    pre = st.session_state.pop("booking_prefill", None)
    if not pre:
        return
    try:
        ci, co = validate_stay_dates(pre["check_in"], pre["check_out"])
    except (ValidationError, KeyError):
        return
    st.session_state["nb_in"] = ci
    st.session_state["nb_out"] = co
    st.session_state["nb_guests"] = int(pre.get("guests", 1))
    available = {r.id for r in ctx.bookings.get_available_rooms(ci, co, int(pre.get("guests", 1)))}
    if pre.get("room_id") in available:
        st.session_state["nb_room"] = pre["room_id"]


def _show_confirmation(ctx, booking_id: int, key: str) -> None:
    details = ctx.bookings.get_booking_details(booking_id)
    if not details:
        return
    orders = ctx.services.list_orders(booking_id)
    text = build_confirmation_text(details, orders)
    st.code(text, language=None)
    c1, c2 = st.columns(2)
    c1.download_button("Download confirmation (.txt)", text, file_name=f"{details['reference']}.txt",
                       mime="text/plain", key=f"dl_txt_{key}")
    c2.download_button("Download confirmation (.html)", build_confirmation_html(details, orders),
                       file_name=f"{details['reference']}.html", mime="text/html", key=f"dl_html_{key}")


def _booking_label(b: dict) -> str:
    return f"{b['reference']} - {b['customer']} - Room {b['room_number']} - {b['check_in']} to {b['check_out']} ({b['status']})"


def render(ctx) -> None:
    hero("Booking Management", "Make reservations, check availability, view details and cancel bookings.")
    show_flash()
    _apply_prefill(ctx)
    tab_new, tab_check, tab_all, tab_details, tab_cancel = st.tabs(
        ["New reservation", "Check availability", "All bookings", "Details and confirmation", "Cancel booking"])
    today = date.today()

    with tab_new:
        c1, c2, c3 = st.columns(3)
        check_in = c1.date_input("Check-in", value=today + timedelta(days=1), min_value=today, key="nb_in")
        check_out = c2.date_input("Check-out", value=today + timedelta(days=2), min_value=today, key="nb_out")
        guests = c3.number_input("Guests", min_value=1, max_value=12, value=2, step=1, key="nb_guests")
        try:
            ci, co = validate_stay_dates(check_in, check_out)
        except ValidationError as exc:
            st.error(str(exc))
        else:
            available = sorted(ctx.bookings.get_available_rooms(ci, co, int(guests)),
                               key=lambda r: r.price_per_night)
            if not available:
                st.warning("No rooms are free for these dates and guests. Try other dates or use **Find a Room**.")
            else:
                ids = [r.id for r in available]
                by_id = {r.id: r for r in available}
                room_id = st.selectbox("Available room", ids, key="nb_room",
                                       format_func=lambda i: f"{by_id[i].label} - {format_money(by_id[i].price_per_night)}/night")
                room = by_id[room_id]
                nights = (co - ci).days
                st.info(f"{nights} night(s) x {format_money(room.price_per_night)} = **{format_money(nights * room.price_per_night)}**")
                g1, g2, g3 = st.columns(3)
                name = g1.text_input("Guest full name", key="nb_name")
                email = g2.text_input("Email", key="nb_email")
                phone = g3.text_input("Phone", key="nb_phone")
                notes = st.text_input("Special requests (optional)", key="nb_notes")
                if st.button("Confirm reservation", key="nb_confirm"):
                    try:
                        booking = ctx.bookings.book_for_guest(name, email, phone, room_id, ci, co, int(guests), notes)
                    except (ValidationError, BookingError) as exc:
                        st.error(str(exc))
                    else:
                        st.success(f"Reservation {booking.reference} confirmed (simulated booking).")
                        _show_confirmation(ctx, booking.id, f"new{booking.id}")

    with tab_check:
        st.caption("Check whether rooms are free for a date range.")
        c1, c2, c3 = st.columns(3)
        ci_in = c1.date_input("From", value=today + timedelta(days=1), min_value=today, key="ck_in")
        co_in = c2.date_input("To", value=today + timedelta(days=2), min_value=today, key="ck_out")
        g = c3.number_input("Guests", min_value=1, max_value=12, value=1, step=1, key="ck_guests")
        rooms = ctx.rooms.list_rooms(active_only=True)
        options = [None] + rooms
        picked = st.selectbox("Specific room (optional)", options, key="ck_room",
                              format_func=lambda r: "All rooms" if r is None else r.label)
        try:
            ci, co = validate_stay_dates(ci_in, co_in)
        except ValidationError as exc:
            st.error(str(exc))
        else:
            if picked is None:
                free = ctx.bookings.get_available_rooms(ci, co, int(g))
                st.success(f"{len(free)} room(s) available.") if free else st.warning("No rooms available.")
                if free:
                    show_table(pd.DataFrame([{"Room": r.room_number, "Name": r.name, "Type": r.accommodation_type,
                                              "Location": r.location, "Price/night": r.price_per_night,
                                              "Capacity": r.capacity} for r in free]))
            elif ctx.bookings.is_available(picked.id, ci, co):
                st.success(f"{picked.label} is available from {ci} to {co}.")
            else:
                st.error(f"{picked.label} is NOT available for these dates.")
                prefs = Preferences(check_in=ci, check_out=co, guests=int(g))
                alts = ctx.recommender.find_alternatives(picked.id, prefs, 3)
                if alts:
                    st.markdown("**Suggested alternatives:**")
                    for alt in alts:
                        room_card(alt)

    bookings = ctx.bookings.list_bookings()
    with tab_all:
        if not bookings:
            st.info("No bookings yet.")
        else:
            status = st.selectbox("Status", ["All", "Confirmed", "Cancelled"], key="all_status")
            term = st.text_input("Search guest, room or reference", key="all_term").strip().lower()
            rows = [b for b in bookings if (status == "All" or b["status"] == status)
                    and (not term or term in b["customer"].lower() or term in b["reference"].lower()
                         or term in str(b["room_number"]).lower())]
            df = pd.DataFrame(rows, columns=["reference", "customer", "room_number", "accommodation_type", "check_in",
                                             "check_out", "nights", "guests", "total_price", "status"])
            show_table(money_df(df, ["total_price"]))
            st.caption(f"{len(rows)} booking(s) shown.")

    with tab_details:
        if not bookings:
            st.info("No bookings yet.")
        else:
            chosen = st.selectbox("Choose a booking", bookings, format_func=_booking_label, key="det_choice")
            _show_confirmation(ctx, chosen["booking_id"], f"det{chosen['booking_id']}")
            orders = ctx.services.list_orders(chosen["booking_id"])
            if orders:
                st.markdown("**Service orders for this booking**")
                show_table(money_df(pd.DataFrame(orders)[["service", "category", "quantity", "total_price", "status"]], ["total_price"]))

    with tab_cancel:
        active = [b for b in bookings if b["status"] == "Confirmed"]
        if not active:
            st.info("There are no confirmed bookings to cancel.")
        else:
            chosen = st.selectbox("Booking to cancel", active, format_func=_booking_label, key="cancel_choice")
            confirm = st.checkbox("Yes, cancel this booking", key="cancel_confirm")
            if st.button("Cancel booking", key="cancel_btn"):
                if not confirm:
                    st.error("Please tick the confirmation box first.")
                else:
                    try:
                        done = ctx.bookings.cancel_booking(chosen["booking_id"])
                    except BookingError as exc:
                        st.error(str(exc))
                    else:
                        flash("success", f"Booking {done.reference} was cancelled. The room is available again.")
                        rerun()