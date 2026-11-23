import pandas as pd
import streamlit as st

from hotel_agent.ai.service_recommender import INTEREST_LABELS
from hotel_agent.config import SERVICE_CATEGORIES, format_money
from hotel_agent.models.entities import Preferences
from hotel_agent.services.service_manager import ServiceError
from hotel_agent.services.validators import ValidationError
from ui.components import flash, hero, money_df, rerun, show_flash, show_table


def render(ctx) -> None:
    hero("Additional Services", "Room service, airport transfers, restaurant tables, spa and more.")
    show_flash()
    tab_cat, tab_order, tab_orders, tab_manage = st.tabs(
        ["Catalogue and suggestions", "Order a service", "Service orders", "Manage services"])
    services = ctx.services.list_services(active_only=True)

    with tab_cat:
        if not services:
            st.info("No services available.")
        for category in sorted({s.category for s in services}):
            st.markdown(f"#### {category}")
            for s in [x for x in services if x.category == category]:
                st.markdown(f"- **{s.name}** - {format_money(s.price)}: {s.description}")
        st.markdown("---")
        st.markdown("#### Which services suit me?")
        interests = st.multiselect("Your interests", list(INTEREST_LABELS), format_func=lambda k: INTEREST_LABELS[k], key="svc_int")
        guests = st.number_input("Guests", min_value=1, max_value=12, value=2, key="svc_guests")
        nights = st.number_input("Nights", min_value=1, max_value=60, value=2, key="svc_nights")
        stay_type = st.selectbox("Room type (optional)", ["Any", "Standard", "Deluxe", "Family", "Executive", "Suite"], key="svc_type")
        prefs = Preferences(guests=int(guests), interests=interests,
                            accommodation_type=None if stay_type == "Any" else stay_type)
        if int(nights) >= 1:
            from datetime import date, timedelta
            prefs.check_in, prefs.check_out = date.today(), date.today() + timedelta(days=int(nights))
        if st.button("Suggest services", key="svc_suggest"):
            suggestions = ctx.service_recommender.recommend(prefs, 5)
            for sug in suggestions:
                st.markdown(f"- **{sug.service.name}** ({format_money(sug.service.price)}) - {sug.reason}")

    with tab_order:
        active = [b for b in ctx.bookings.list_bookings("Confirmed")]
        if not active or not services:
            st.info("You need at least one confirmed booking and one active service to place an order.")
        else:
            booking = st.selectbox("Booking", active, key="ord_booking",
                                   format_func=lambda b: f"{b['reference']} - {b['customer']} - Room {b['room_number']}")
            service = st.selectbox("Service", services, key="ord_service",
                                   format_func=lambda s: f"{s.name} ({s.category}) - {format_money(s.price)}")
            qty = st.number_input("Quantity", min_value=1, max_value=50, value=1, key="ord_qty")
            details = st.text_input("Details (time, preferences)", key="ord_details")
            st.caption(f"Total: {format_money(service.price * int(qty))}")
            if st.button("Place order", key="ord_btn"):
                try:
                    ctx.services.order_service(booking["booking_id"], service.id, int(qty), details)
                except (ValidationError, ServiceError) as exc:
                    st.error(str(exc))
                else:
                    flash("success", f"Ordered {int(qty)} x {service.name} for {booking['reference']} (simulated).")
                    rerun()

    with tab_orders:
        orders = ctx.services.list_orders()
        if not orders:
            st.info("No service orders yet.")
        else:
            show_table(money_df(pd.DataFrame(orders), ["total_price"]))
            open_orders = [o for o in orders if o["status"] != "Cancelled"]
            if open_orders:
                chosen = st.selectbox("Cancel an order", open_orders, key="ord_cancel",
                                      format_func=lambda o: f"#{o['id']} - {o['service']} (booking {o['booking_id']})")
                if st.button("Cancel order", key="ord_cancel_btn"):
                    try:
                        ctx.services.cancel_order(chosen["id"])
                    except ServiceError as exc:
                        st.error(str(exc))
                    else:
                        flash("success", "Order cancelled.")
                        rerun()

    with tab_manage:
        with st.form("add_service_form"):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("Service name")
            category = c2.selectbox("Category", SERVICE_CATEGORIES)
            price = c3.number_input("Price", min_value=0.0, value=20.0, step=5.0)
            description = st.text_input("Description")
            if st.form_submit_button("Add service"):
                try:
                    ctx.services.add_service(name, category, price, description)
                except (ValidationError, ServiceError) as exc:
                    st.error(str(exc))
                else:
                    flash("success", f"Service '{name.strip()}' added.")
                    rerun()
        all_services = ctx.services.list_services(active_only=False)
        if all_services:
            chosen = st.selectbox("Enable or disable a service", all_services, key="svc_toggle",
                                  format_func=lambda s: f"{s.name} ({'active' if s.is_active else 'disabled'})")
            if st.button("Toggle active status", key="svc_toggle_btn"):
                ctx.services.set_active(chosen.id, not chosen.is_active)
                flash("success", f"{chosen.name} is now {'disabled' if chosen.is_active else 'active'}.")
                rerun()