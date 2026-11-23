"""Initial hotel data used to populate an empty database."""
from datetime import date, timedelta

from hotel_agent.database.connection import Database

INITIAL_NOTE = "Initial booking"

# (room_number, name, type, location, price, capacity, amenities, description)
DEMO_ROOMS = [
    ("101", "City Standard Queen", "Standard", "City Centre", 60, 2,
     "WiFi, Air Conditioning, TV, Work Desk", "Compact queen room close to shops and cafes."),
    ("102", "City Standard Plus", "Standard", "City Centre", 68, 2,
     "WiFi, Air Conditioning, TV, Work Desk, Breakfast", "Standard room with breakfast included."),
    ("103", "Garden Standard", "Standard", "Garden Wing", 55, 2,
     "WiFi, Air Conditioning, TV", "Quiet room overlooking the courtyard garden."),
    ("104", "Airport Standard", "Standard", "Airport Side", 58, 2,
     "WiFi, Air Conditioning, TV, Parking, Work Desk", "Practical room for early flights."),
    ("201", "City Deluxe", "Deluxe", "City Centre", 110, 3,
     "WiFi, Air Conditioning, TV, Balcony, Mini Bar, Work Desk", "Spacious deluxe room with a city balcony."),
    ("202", "Beach Deluxe", "Deluxe", "Beachfront", 135, 3,
     "WiFi, Air Conditioning, TV, Balcony, Sea View, Mini Bar, Breakfast", "Deluxe room with a sea-view balcony."),
    ("203", "Garden Deluxe", "Deluxe", "Garden Wing", 105, 3,
     "WiFi, Air Conditioning, TV, Balcony, Bathtub", "Relaxing deluxe room with a bathtub."),
    ("204", "Airport Deluxe", "Deluxe", "Airport Side", 100, 2,
     "WiFi, Air Conditioning, TV, Mini Bar, Parking", "Soundproofed deluxe room near the terminal."),
    ("301", "Garden Family Room", "Family", "Garden Wing", 150, 5,
     "WiFi, Air Conditioning, TV, Kitchenette, Breakfast, Pool Access", "Two bedrooms, ideal for families."),
    ("302", "Beach Family Suite", "Family", "Beachfront", 175, 6,
     "WiFi, Air Conditioning, TV, Kitchenette, Sea View, Balcony, Pool Access", "Large family room facing the sea."),
    ("303", "City Family Room", "Family", "City Centre", 160, 5,
     "WiFi, Air Conditioning, TV, Kitchenette, Breakfast", "Family room within walking distance of attractions."),
    ("401", "Executive City Room", "Executive", "City Centre", 210, 2,
     "WiFi, Air Conditioning, TV, Work Desk, Lounge Access, Mini Bar, Breakfast, Gym Access", "Business-focused room with lounge access."),
    ("402", "Executive Airport Room", "Executive", "Airport Side", 195, 2,
     "WiFi, Air Conditioning, TV, Work Desk, Lounge Access, Parking, Breakfast", "Executive comfort next to the airport."),
    ("501", "Beach Panorama Suite", "Suite", "Beachfront", 320, 4,
     "WiFi, Air Conditioning, TV, Sea View, Balcony, Bathtub, Mini Bar, Lounge Access, Breakfast, Pool Access",
     "Top-floor suite with a panoramic sea view."),
    ("502", "City Skyline Suite", "Suite", "City Centre", 290, 3,
     "WiFi, Air Conditioning, TV, Balcony, Bathtub, Mini Bar, Lounge Access, Work Desk, Breakfast",
     "Suite with a skyline view and separate lounge."),
    ("503", "Garden Villa Suite", "Suite", "Garden Wing", 270, 4,
     "WiFi, Air Conditioning, TV, Balcony, Bathtub, Kitchenette, Pool Access, Breakfast",
     "Private suite opening onto the garden."),
]

# (name, category, price, description)
DEMO_SERVICES = [
    ("In-Room Dining", "Room Service", 18, "Hot meal delivered to your room (per order)."),
    ("Late-Night Snack Tray", "Room Service", 12, "Light snacks and drinks after 10 pm."),
    ("Airport Transfer (One Way)", "Airport Transfer", 35, "Private car between the airport and the hotel."),
    ("Airport Transfer (Return)", "Airport Transfer", 60, "Private car both ways."),
    ("Dinner Table Reservation", "Restaurant", 25, "Reserved table with a welcome drink (per booking)."),
    ("Romantic Dinner Package", "Restaurant", 80, "Three-course dinner for two with candles and music."),
    ("Relaxation Massage (60 min)", "Spa", 70, "One-hour full-body massage."),
    ("Spa Day Pass", "Spa", 45, "Access to sauna, steam room and relaxation lounge."),
    ("Laundry Service", "Laundry", 20, "Wash and fold, returned within 24 hours."),
    ("Business Centre Pack", "Business", 25, "Printing, scanning and a private meeting space (2 hours)."),
    ("Guided City Tour", "Tour", 40, "Half-day guided tour of local highlights."),
    ("Kids Club Session", "Childcare", 30, "Supervised activities for children aged 4-10 (per session)."),
]

DEMO_CUSTOMERS = [
    ("Demo Guest Amina", "amina.demo@example.com", "+254 700 000 001"),
    ("Demo Guest Brian", "brian.demo@example.com", "+254 700 000 002"),
    ("Demo Guest Carla", "carla.demo@example.com", "+254 700 000 003"),
    ("Demo Guest David", "david.demo@example.com", "+254 700 000 004"),
]

# (room_number, customer_index, start_offset_days, end_offset_days, guests, status)
DEMO_BOOKINGS = [
    ("101", 0, -30, -27, 2, "Confirmed"),
    ("202", 1, -21, -18, 2, "Confirmed"),
    ("301", 2, -14, -10, 4, "Confirmed"),
    ("401", 3, -9, -7, 1, "Confirmed"),
    ("501", 0, -5, -2, 2, "Confirmed"),
    ("201", 1, -1, 2, 2, "Confirmed"),
    ("102", 2, 0, 3, 2, "Confirmed"),
    ("302", 3, 5, 9, 5, "Confirmed"),
    ("502", 0, 10, 12, 2, "Confirmed"),
    ("203", 1, 3, 5, 2, "Cancelled"),
]


def seed_demo_data(db: Database) -> bool:
    """Insert initial data when the database is empty. Returns True if data was added."""
    if db.query_one("SELECT COUNT(*) AS c FROM rooms")["c"] > 0:
        return False
    for r in DEMO_ROOMS:
        db.execute(
            """INSERT INTO rooms (room_number, name, accommodation_type, location, price_per_night,
                                  capacity, amenities, description, is_active)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)""", r)
    for s in DEMO_SERVICES:
        db.execute("INSERT INTO services (name, category, price, description, is_active) VALUES (?, ?, ?, ?, 1)", s)
    customer_ids = [
        db.execute("INSERT INTO customers (full_name, email, phone) VALUES (?, ?, ?)", c)
        for c in DEMO_CUSTOMERS
    ]
    today = date.today()
    booking_ids = []
    for room_number, cust_idx, start, end, guests, status in DEMO_BOOKINGS:
        room = db.query_one("SELECT id, price_per_night FROM rooms WHERE room_number = ?", (room_number,))
        ci, co = today + timedelta(days=start), today + timedelta(days=end)
        total = round((co - ci).days * room["price_per_night"], 2)
        booking_ids.append(db.execute(
            """INSERT INTO bookings (customer_id, room_id, check_in, check_out, guests,
                                     total_price, status, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (customer_ids[cust_idx], room["id"], ci.isoformat(), co.isoformat(), guests, total, status, INITIAL_NOTE)))
    spa = db.query_one("SELECT id, price FROM services WHERE name = 'Relaxation Massage (60 min)'")
    dining = db.query_one("SELECT id, price FROM services WHERE name = 'Romantic Dinner Package'")
    transfer = db.query_one("SELECT id, price FROM services WHERE name = 'Airport Transfer (Return)'")
    for booking_id, svc, qty, status in [(booking_ids[4], spa, 2, "Completed"),
                                         (booking_ids[5], dining, 1, "Requested"),
                                         (booking_ids[7], transfer, 1, "Requested")]:
        db.execute(
            """INSERT INTO service_orders (booking_id, service_id, quantity, total_price, details, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (booking_id, svc["id"], qty, svc["price"] * qty, INITIAL_NOTE, status))
    return True