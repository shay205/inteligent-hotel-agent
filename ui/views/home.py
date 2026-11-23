import streamlit as st

from hotel_agent.config import HOTEL_FACILITIES, HOTEL_NAME, format_money
from ui.components import navigate


HERO_IMAGE = (
    "https://images.unsplash.com/photo-1566073771259-6a8506099945"
    "?auto=format&fit=crop&w=2400&q=92"
)


def render(ctx) -> None:
    st.markdown(
        f"<section class='luxury-hero' style=\"background-image:"
        f"linear-gradient(90deg, rgba(20,15,12,.62), rgba(20,15,12,.06)),"
        f"url('{HERO_IMAGE}')\">"
        "<div class='luxury-hero-content'>"
        "<p class='hero-kicker'>A private world of effortless luxury</p>"
        f"<h1>{HOTEL_NAME}</h1>"
        "<p class='hero-copy'>Thoughtful service, refined interiors and memorable stays "
        "in the heart of the city.</p>"
        "<div class='hero-actions'>"
        "<span class='hero-primary'>Reserve a room</span>"
        "<span class='hero-secondary'>Discover the hotel</span>"
        "</div></div></section>",
        unsafe_allow_html=True)

    if st.button("Book now", key="home_book_now"):
        navigate("Rooms")

    st.markdown("<div class='section-heading'><p>Curated for you</p><h2>Stay beautifully</h2></div>",
                unsafe_allow_html=True)
    rooms = ctx.rooms.list_rooms(active_only=True)
    if not rooms:
        st.caption("Room collection is being prepared.")
    else:
        featured = sorted(rooms, key=lambda r: r.price_per_night)[:3]
        cols = st.columns(3)
        room_images = [
            "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=1200&q=92",
            "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=92",
            "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1200&q=92",
        ]
        for col, room, image in zip(cols, featured, room_images):
            with col:
                st.markdown(
                    f"<article class='room-feature-card'>"
                    f"<div class='room-feature-image' style=\"background-image:url('{image}')\"></div>"
                    f"<div class='room-feature-body'><p>{room.accommodation_type} · "
                    f"Up to {room.capacity} guests</p><h3>{room.name}</h3>"
                    f"<div class='room-feature-meta'><span>{room.location}</span>"
                    f"<strong>{format_money(room.price_per_night)} <small>/ night</small></strong></div>"
                    f"</div></article>",
                    unsafe_allow_html=True)
                if st.button("Explore room", key=f"home_room_{room.id}", width="stretch"):
                    navigate("Rooms")

    st.markdown("<div class='section-heading amenity-heading'><p>Everything considered</p>"
                "<h2>Hotel amenities</h2></div>", unsafe_allow_html=True)
    amenities = HOTEL_FACILITIES
    cols = st.columns(4)
    amenity_images = [
        "https://images.unsplash.com/photo-1540541338287-41700207dee6?auto=format&fit=crop&w=1200&q=92",
        "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=1200&q=92",
        "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=1200&q=92",
        "https://images.unsplash.com/photo-1544161515-4ab6ce6db874?auto=format&fit=crop&w=1200&q=92",
    ]
    for i, (facility, image) in enumerate(zip(amenities[:4], amenity_images)):
        with cols[i % 4]:
            st.markdown(
                f"<article class='amenity-card' style=\"background-image:"
                f"linear-gradient(180deg, rgba(20,15,12,.08), rgba(20,15,12,.82)),"
                f"url('{image}')\">"
                "<div class='amenity-card-content'><span>Luxury Grand Hotel</span>"
                f"<h3>{facility}</h3></div></article>",
                unsafe_allow_html=True)

    st.markdown(
        "<section class='guest-promise'><p class='hero-kicker'>The Luxury Grand standard</p>"
        "<h2>Designed around how you want to feel</h2>"
        "<p>From the first welcome to the final farewell, every detail is shaped to feel "
        "personal, calm and effortlessly comfortable.</p></section>",
        unsafe_allow_html=True)

    left, right = st.columns([2, 1])
    with left:
        st.markdown("<div class='contact-card'><p class='eyebrow'>Contact</p>"
                    "<h2>Your stay, personally arranged</h2>"
                    "<p>Use the hotel concierge for availability, facilities and reservation guidance.</p></div>",
                    unsafe_allow_html=True)
    with right:
        if st.button("Message the concierge", key="home_concierge", width="stretch"):
            navigate("AI Concierge")

    st.markdown("<footer class='luxury-footer'>"
                f"<strong>{HOTEL_NAME}</strong><span>Hotel &amp; Residences</span>"
                "<span>Guest assistance available through the concierge</span></footer>",
                unsafe_allow_html=True)
