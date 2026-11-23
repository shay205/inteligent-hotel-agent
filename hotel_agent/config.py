"""Central configuration: paths, constants and scoring weights.

Keeping every "magic number" here means you can explain (and tune) the
behaviour of the system from one place.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "hotel.db"

HOTEL_NAME = "Luxury Grand Hotel"
CURRENCY = "$"
CHECK_IN_TIME = "14:00"
CHECK_OUT_TIME = "11:00"
MAX_STAY_NIGHTS = 60
MAX_GUESTS = 12

ACCOMMODATION_TYPES = ["Standard", "Deluxe", "Family", "Executive", "Suite"]

# How "luxurious" each type is. Used to give partial credit when a customer
# asks for a type that does not exist / is unavailable (e.g. Deluxe vs Suite).
TYPE_RANK = {"Standard": 1, "Deluxe": 2, "Family": 2, "Executive": 3, "Suite": 4}

# Recommendation score weights (they add up to 100).
SCORING_WEIGHTS = {
    "location": 30,
    "budget": 25,
    "type": 20,
    "capacity": 15,
    "amenities": 10,
}
MIN_RECOMMENDATION_SCORE = 35.0

AMENITY_OPTIONS = [
    "WiFi", "Air Conditioning", "TV", "Breakfast", "Balcony", "Sea View",
    "Pool Access", "Mini Bar", "Bathtub", "Kitchenette", "Work Desk",
    "Lounge Access", "Parking", "Gym Access",
]

SERVICE_CATEGORIES = [
    "Room Service", "Airport Transfer", "Restaurant", "Spa",
    "Laundry", "Business", "Tour", "Childcare", "Other",
]

HOTEL_FACILITIES = [
    "Outdoor swimming pool", "Fitness centre", "Restaurant and bar", "Spa and wellness centre",
    "Free WiFi in all areas", "On-site parking", "24-hour reception", "Airport transfer service",
]

BOOKING_STATUSES = ["Confirmed", "Cancelled"]


def format_money(value) -> str:
    """Format a number as money, e.g. 1234.5 -> $1,234.50."""
    try:
        return f"{CURRENCY}{float(value):,.2f}"
    except (TypeError, ValueError):
        return f"{CURRENCY}0.00"