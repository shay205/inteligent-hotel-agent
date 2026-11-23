from datetime import date, timedelta

import streamlit as st

from hotel_agent.config import format_money
from ui.components import hero, money_df, show_table


def _download(ctx, df, name: str, key: str) -> None:
    st.download_button("Download CSV", ctx.reports.to_csv_bytes(df), file_name=f"{name}.csv",
                       mime="text/csv", key=key)


def render(ctx) -> None:
    hero("Reports and Analytics", "Customer, booking, occupancy and revenue reports built with pandas.")
    tab_c, tab_b, tab_o, tab_r = st.tabs(["Customers", "Bookings", "Room occupancy", "Revenue"])

    with tab_c:
        df = ctx.reports.customer_report()
        if df.empty:
            st.info("No customers yet.")
        else:
            show_table(money_df(df, ["Room spend", "Service spend", "Total spend"]))
            st.bar_chart(df.set_index("Customer")["Total spend"])
            _download(ctx, df, "customer_report", "dl_cust")

    with tab_b:
        c1, c2, c3 = st.columns(3)
        status = c1.selectbox("Status", ["All", "Confirmed", "Cancelled"], key="rb_status")
        start = c2.date_input("Stays from", value=date.today() - timedelta(days=60), key="rb_start")
        end = c3.date_input("Stays until", value=date.today() + timedelta(days=60), key="rb_end")
        df = ctx.reports.booking_report(status, start, end)
        if df.empty:
            st.info("No bookings match these filters.")
        else:
            show_table(money_df(df, ["total_price"]))
            st.caption(f"{len(df)} booking(s), total value {format_money(df['total_price'].sum())}")
            _download(ctx, df, "booking_report", "dl_book")

    with tab_o:
        c1, c2 = st.columns(2)
        start = c1.date_input("Period start", value=date.today() - timedelta(days=30), key="ro_start")
        end = c2.date_input("Period end", value=date.today() + timedelta(days=30), key="ro_end")
        if end < start:
            st.error("The period end must not be before the start.")
        else:
            daily = ctx.reports.daily_occupancy(start, end)
            st.markdown("**Daily occupancy (%)**")
            st.line_chart(daily.set_index("Date")["Occupancy %"])
            rooms = ctx.reports.room_occupancy(start, end)
            st.markdown("**Occupancy per room**")
            show_table(rooms)
            st.caption(f"Average occupancy over the period: {daily['Occupancy %'].mean():.1f}%")
            _download(ctx, rooms, "room_occupancy", "dl_occ")

    with tab_r:
        s = ctx.reports.revenue_summary()
        a, b, c, d = st.columns(4)
        a.metric("Total revenue", format_money(s["total"]))
        b.metric("Room revenue", format_money(s["rooms"]))
        c.metric("Service revenue", format_money(s["services"]))
        d.metric("Cancelled value", format_money(s["cancelled_value"]))
        monthly = ctx.reports.revenue_by_month()
        by_type = ctx.reports.revenue_by_room_type()
        by_svc = ctx.reports.revenue_by_service_category()
        if not monthly.empty:
            st.markdown("**Room revenue by month (by check-in month)**")
            st.bar_chart(monthly.set_index("Month")["Revenue"])
            show_table(money_df(monthly, ["Revenue"]))
        if not by_type.empty:
            st.markdown("**By room type**")
            show_table(money_df(by_type, ["Revenue"]))
        if not by_svc.empty:
            st.markdown("**By service category**")
            show_table(money_df(by_svc, ["Revenue"]))
        if not monthly.empty:
            _download(ctx, monthly, "revenue_by_month", "dl_rev")