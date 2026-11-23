import streamlit as st

from hotel_agent.config import HOTEL_NAME, format_money
from ui.components import hero, metric_card, money_df, navigate, show_table


def render(ctx) -> None:
    hero("Hotel overview", "A live view of guests, rooms, reservations and revenue.")
    m = ctx.reports.dashboard_metrics()
    customer_count = len(ctx.customers.list_customers())
    bookings = ctx.reports.bookings_df()
    from datetime import date
    upcoming = len(bookings[(bookings["status"] == "Confirmed") &
                            (bookings["check_in"] >= date.today().isoformat())])
    cards = st.columns(5)
    with cards[0]:
        metric_card("Registered guests", customer_count, "real customer records")
    with cards[1]:
        metric_card("Total bookings", m["total_bookings"], f"{m['cancelled_bookings']} cancelled")
    with cards[2]:
        metric_card("Available rooms", m["available_rooms"], "available today")
    with cards[3]:
        metric_card("Occupied rooms", m["occupied_rooms"], f"{m['occupancy_pct']}% occupancy")
    with cards[4]:
        metric_card("Upcoming stays", upcoming, "confirmed reservations")

    st.markdown("### Registered members")
    customers = ctx.customers.list_customers()
    if not customers:
        st.caption("No registered members yet.")
    else:
        member_rows = []
        for customer in customers:
            member_rows.append(
                f"<div class='member-row'><span class='member-avatar'>"
                f"{customer['full_name'][:1].upper()}</span><div><strong>"
                f"{customer['full_name']}</strong><small>{customer['email']}"
                f"{' · ' + customer['phone'] if customer['phone'] else ''}</small>"
                f"</div></div>")
        st.markdown("<div class='member-list'>" + "".join(member_rows) + "</div>",
                    unsafe_allow_html=True)

    st.markdown("### Recent bookings")
    recent = ctx.reports.recent_bookings(6)
    if recent.empty:
        st.info("No bookings yet. Use **Find a Room** to make the first reservation.")
    else:
        show_table(money_df(recent, ["total_price"]).rename(columns={
            "reference": "Reference", "customer": "Guest", "room_number": "Room",
            "accommodation_type": "Type", "check_in": "Check-in", "check_out": "Check-out",
            "total_price": "Total", "status": "Status"}))

    left, right = st.columns(2)
    with left:
        st.markdown("### Revenue by month")
        monthly = ctx.reports.revenue_by_month()
        if monthly.empty:
            st.caption("No revenue data yet.")
        else:
            st.bar_chart(monthly.set_index("Month")["Revenue"])
    with right:
        st.markdown("### Revenue by room type")
        by_type = ctx.reports.revenue_by_room_type()
        if by_type.empty:
            st.caption("No revenue data yet.")
        else:
            st.bar_chart(by_type.set_index("Room type")["Revenue"])

    st.markdown("### Quick actions")
    a, b, c = st.columns(3)
    if a.button("Find a room", key="qa_find"):
        navigate("Rooms")
    if b.button("Ask the assistant", key="qa_chat"):
        navigate("AI Concierge")
    if c.button("Manage bookings", key="qa_book"):
        navigate("My Bookings")