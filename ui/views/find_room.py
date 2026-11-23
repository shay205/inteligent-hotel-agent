from datetime import date, timedelta

import streamlit as st

from hotel_agent.ai.service_recommender import INTEREST_LABELS
from hotel_agent.config import ACCOMMODATION_TYPES, AMENITY_OPTIONS, format_money
from hotel_agent.models.entities import Preferences
from hotel_agent.services.validators import ValidationError, validate_guests, validate_stay_dates
from ui.components import hero, navigate, optional, room_card, show_flash, show_table
import pandas as pd


def _breakdown_table(rec) -> pd.DataFrame:
    return pd.DataFrame([{"Category": k.capitalize(), "Points": v} for k, v in rec.breakdown.items()])


def render(ctx) -> None:
    hero("Find a Room", "Tell us what you need. We rank every available room and explain why.")
    show_flash()
    today = date.today()
    locations = ["Any"] + ctx.rooms.get_locations()
    types = ["Any"] + [t for t in ACCOMMODATION_TYPES if t in ctx.rooms.get_types()]

    with st.form("preferences_form"):
        c1, c2, c3 = st.columns(3)
        location = c1.selectbox("Preferred location", locations)
        acc_type = c2.selectbox("Accommodation type", types)
        budget = c3.number_input("Maximum budget per night (0 = no limit)", min_value=0.0, value=150.0, step=10.0)
        c4, c5, c6 = st.columns(3)
        check_in = c4.date_input("Check-in date", value=today + timedelta(days=1), min_value=today)
        check_out = c5.date_input("Check-out date", value=today + timedelta(days=3), min_value=today)
        guests = c6.number_input("Number of guests", min_value=1, max_value=12, value=2, step=1)
        amenities = st.multiselect("Must-have amenities (optional)", AMENITY_OPTIONS)
        interests = st.multiselect("Interests, used to suggest services (optional)", list(INTEREST_LABELS),
                                   format_func=lambda k: INTEREST_LABELS[k])
        submitted = st.form_submit_button("Find my room")

    if submitted:
        try:
            ci, co = validate_stay_dates(check_in, check_out)
            validate_guests(guests)
        except ValidationError as exc:
            st.error(str(exc))
            st.session_state.pop("find_state", None)
        else:
            prefs = Preferences(
                location=optional(location), budget=float(budget) if budget > 0 else None,
                accommodation_type=optional(acc_type), check_in=ci, check_out=co,
                guests=int(guests), amenities=amenities, interests=interests)
            all_recs = ctx.recommender.recommend(prefs, include_unavailable=True)
            available = [r for r in all_recs if r.available]
            note = ""
            if not available:
                available, note = ctx.recommender.recommend_with_fallback(prefs)
            st.session_state["find_state"] = {
                "prefs": prefs, "available": available,
                "unavailable": [r for r in all_recs if not r.available], "note": note}

    state = st.session_state.get("find_state")
    if not state:
        st.info("Fill in the form and press **Find my room** to see recommendations.")
        return

    prefs = state["prefs"]
    st.markdown(f"### Results for {prefs.check_in} to {prefs.check_out} ({prefs.nights} night(s), {prefs.guests} guest(s))")
    if state["note"]:
        st.warning(state["note"])

    f1, f2, f3 = st.columns(3)
    sort_by = f1.selectbox("Sort by", ["Best match", "Lowest price", "Highest price"])
    min_score = f2.slider("Minimum match score", 0, 100, 0)
    text = f3.text_input("Search name or amenity")

    recs = [r for r in state["available"] if r.score >= min_score]
    if text.strip():
        needle = text.strip().lower()
        recs = [r for r in recs if needle in r.room.name.lower() or needle in r.room.amenities_text.lower()
                or needle in r.room.accommodation_type.lower() or needle in r.room.location.lower()]
    if sort_by == "Lowest price":
        recs.sort(key=lambda r: r.room.price_per_night)
    elif sort_by == "Highest price":
        recs.sort(key=lambda r: -r.room.price_per_night)

    if not recs:
        st.info("No rooms match these filters. Try lowering the minimum score or clearing the search.")
    for rank, rec in enumerate(recs, start=1):
        st.markdown(f"**#{rank}**")
        room_card(rec)
        cols = st.columns([1, 1, 3])
        total = rec.room.price_per_night * prefs.nights
        cols[2].caption(f"Estimated room total: {format_money(total)} for {prefs.nights} night(s)")
        if cols[0].button("Book this room", key=f"book_{rec.room.id}"):
            navigate("My Bookings", room_id=rec.room.id, check_in=prefs.check_in,
                     check_out=prefs.check_out, guests=prefs.guests)
        with cols[1].expander("Score details"):
            show_table(_breakdown_table(rec))

    if state["unavailable"]:
        with st.expander(f"Rooms that match but are booked for these dates ({len(state['unavailable'])})"):
            for rec in state["unavailable"][:5]:
                room_card(rec)
            first = state["unavailable"][0]
            alts = ctx.recommender.find_alternatives(first.room.id, prefs, 3)
            if alts:
                st.markdown(f"**Alternatives to Room {first.room.room_number}:**")
                for alt in alts:
                    room_card(alt)

    st.markdown("### Suggested additional services")
    suggestions = ctx.service_recommender.recommend(
        prefs if not recs else _prefs_with_top_room(prefs, recs[0]), 4)
    if not suggestions:
        st.caption("No service suggestions available.")
    for s in suggestions:
        st.markdown(f"- **{s.service.name}** ({format_money(s.service.price)}): {s.reason}")


def _prefs_with_top_room(prefs: Preferences, top) -> Preferences:
    """Use the best room's type/location when the customer left them as 'Any'."""
    from dataclasses import replace
    return replace(prefs, location=prefs.location or top.room.location,
                   accommodation_type=prefs.accommodation_type or top.room.accommodation_type)