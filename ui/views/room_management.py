from datetime import date

import pandas as pd
import streamlit as st

from hotel_agent.config import ACCOMMODATION_TYPES, AMENITY_OPTIONS
from hotel_agent.services.room_manager import RoomError
from hotel_agent.services.validators import ValidationError
from ui.components import flash, hero, rerun, show_flash, show_table


def _room_form_fields(prefix: str, room=None):
    c1, c2, c3 = st.columns(3)
    number = c1.text_input("Room number", value=room.room_number if room else "", key=f"{prefix}_num")
    name = c2.text_input("Room name", value=room.name if room else "", key=f"{prefix}_name")
    types = ACCOMMODATION_TYPES
    acc = c3.selectbox("Accommodation type", types, index=types.index(room.accommodation_type) if room else 0,
                       key=f"{prefix}_type")
    c4, c5, c6 = st.columns(3)
    location = c4.text_input("Location", value=room.location if room else "", key=f"{prefix}_loc")
    price = c5.number_input("Price per night", min_value=1.0, value=float(room.price_per_night) if room else 100.0,
                            step=5.0, key=f"{prefix}_price")
    capacity = c6.number_input("Capacity (guests)", min_value=1, max_value=12,
                               value=int(room.capacity) if room else 2, step=1, key=f"{prefix}_cap")
    options = sorted(set(AMENITY_OPTIONS) | set(room.amenities if room else []))
    amenities = st.multiselect("Amenities", options, default=room.amenities if room else [], key=f"{prefix}_am")
    description = st.text_input("Description", value=room.description if room else "", key=f"{prefix}_desc")
    return number, name, acc, location, price, capacity, amenities, description


def render(ctx) -> None:
    hero("Room Management", "Add, edit, delete and review the availability of rooms.")
    show_flash()
    tab_list, tab_add, tab_edit, tab_delete = st.tabs(["Rooms and availability", "Add room", "Edit room", "Delete room"])

    with tab_list:
        day = st.date_input("Show availability on", value=date.today(), key="rm_day")
        table = pd.DataFrame(ctx.rooms.availability_table(day))
        if table.empty:
            st.info("No rooms yet. Add one in the **Add room** tab.")
        else:
            status = st.multiselect("Filter by status", ["Available", "Occupied", "Inactive"],
                                    default=["Available", "Occupied", "Inactive"])
            table = table[table["Status"].isin(status)]
            show_table(table)
            counts = pd.DataFrame(ctx.rooms.availability_table(day))["Status"].value_counts()
            st.caption(" | ".join(f"{k}: {v}" for k, v in counts.items()))

    with tab_add:
        with st.form("add_room_form", clear_on_submit=False):
            number, name, acc, loc, price, cap, am, desc = _room_form_fields("add")
            if st.form_submit_button("Add room"):
                try:
                    ctx.rooms.add_room(number, name, acc, loc, price, cap, am, desc)
                except (ValidationError, RoomError) as exc:
                    st.error(str(exc))
                else:
                    flash("success", f"Room {number.strip()} was added.")
                    rerun()

    rooms = ctx.rooms.list_rooms()
    with tab_edit:
        if not rooms:
            st.info("There are no rooms to edit.")
        else:
            chosen = st.selectbox("Choose a room to edit", rooms, format_func=lambda r: r.label, key="edit_choice")
            with st.form(f"edit_room_form_{chosen.id}"):
                number, name, acc, loc, price, cap, am, desc = _room_form_fields(f"edit{chosen.id}", chosen)
                active = st.checkbox("Room is active (can be booked)", value=chosen.is_active, key=f"edit{chosen.id}_act")
                if st.form_submit_button("Save changes"):
                    try:
                        ctx.rooms.update_room(chosen.id, room_number=number, name=name, accommodation_type=acc,
                                              location=loc, price_per_night=price, capacity=cap,
                                              amenities=am, description=desc, is_active=active)
                    except (ValidationError, RoomError) as exc:
                        st.error(str(exc))
                    else:
                        flash("success", f"Room {number.strip()} was updated.")
                        rerun()

    with tab_delete:
        if not rooms:
            st.info("There are no rooms to delete.")
        else:
            chosen = st.selectbox("Choose a room to delete", rooms, format_func=lambda r: r.label, key="del_choice")
            st.warning("Rooms that have booking history cannot be deleted; deactivate them instead.")
            confirm = st.checkbox("I understand this cannot be undone", key="del_confirm")
            if st.button("Delete room", key="del_btn"):
                if not confirm:
                    st.error("Please tick the confirmation box first.")
                else:
                    try:
                        ctx.rooms.delete_room(chosen.id)
                    except RoomError as exc:
                        st.error(str(exc))
                    else:
                        flash("success", f"Room {chosen.room_number} was deleted.")
                        rerun()