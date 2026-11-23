"""AI-Powered Intelligent Hotel Booking and Guest Assistance Agent.

Run with:   streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="Luxury Grand Hotel - AI Booking Agent", page_icon="🏨", layout="wide")

from hotel_agent.app_context import build_context  # noqa: E402
from hotel_agent.config import HOTEL_NAME  # noqa: E402
from ui.styles import inject_css  # noqa: E402
from ui.views import (additional_services, assistant, booking_management, dashboard,  # noqa: E402
                      find_room, home, reports_analytics, room_management)
from ui.components import rerun  # noqa: E402

PAGES = {
    "Home": home,
    "Rooms": find_room,
    "My Bookings": booking_management,
    "AI Concierge": assistant,
    "About & Contact": home,
    "Dashboard": dashboard,
    "Room Management": room_management,
    "Additional Services": additional_services,
    "Reports and Analytics": reports_analytics,
}


@st.cache_resource
def get_context():
    return build_context()


def main() -> None:
    inject_css()
    ctx = get_context()
    if "_goto" in st.session_state:          # set by navigate(); must happen before the radio is created
        st.session_state["nav_page"] = st.session_state.pop("_goto")
    with st.sidebar:
        st.markdown(
            f"<div class='brand-mark'><span class='brand-monogram'>LG</span>"
            f"<div><div class='brand-name'>{HOTEL_NAME}</div>"
            "<div class='brand-caption'>Hotel &amp; Residences</div></div></div>",
            unsafe_allow_html=True)
        page = st.radio("Explore", list(PAGES), key="nav_page", label_visibility="collapsed")
        st.markdown("<div class='sidebar-footer'>Private. Personal. Exceptional.</div>",
                    unsafe_allow_html=True)
    try:
        PAGES[page].render(ctx)
    except Exception as exc:  # last line of defence: show a friendly message instead of a crash
        st.error(f"Something went wrong on this page: {exc}")
        st.exception(exc)
    if st.button(":material/chat:  Ask the concierge", key="floating_ai"):
        st.session_state["_goto"] = "AI Concierge"
        rerun()


main()