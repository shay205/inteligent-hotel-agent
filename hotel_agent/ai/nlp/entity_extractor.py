"""Pull useful details (prices, dates, guests, room types ...) out of a message."""
import re
from datetime import date, timedelta
from typing import Dict, Iterable, List, Optional

NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
                "seven": 7, "eight": 8, "nine": 9, "ten": 10}
_NUM = r"(\d{1,2}|" + "|".join(NUMBER_WORDS) + r")"

MONTHS = {"january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3, "april": 4,
          "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7, "august": 8, "aug": 8,
          "september": 9, "sept": 9, "sep": 9, "october": 10, "oct": 10, "november": 11,
          "nov": 11, "december": 12, "dec": 12}
_MONTH_PAT = "|".join(sorted(MONTHS, key=len, reverse=True))
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

AMENITY_SYNONYMS = {
    "wifi": "WiFi", "wi-fi": "WiFi", "internet": "WiFi",
    "air conditioning": "Air Conditioning", "aircon": "Air Conditioning",
    "tv": "TV", "television": "TV", "breakfast": "Breakfast", "balcony": "Balcony",
    "sea view": "Sea View", "ocean view": "Sea View", "beach view": "Sea View",
    "swimming pool": "Pool Access", "pool": "Pool Access",
    "mini bar": "Mini Bar", "minibar": "Mini Bar", "bathtub": "Bathtub",
    "kitchenette": "Kitchenette", "kitchen": "Kitchenette",
    "work desk": "Work Desk", "desk": "Work Desk", "lounge": "Lounge Access",
    "parking": "Parking", "gym": "Gym Access", "fitness": "Gym Access",
}

LOCATION_SYNONYMS = {
    "city center": "City Centre", "downtown": "City Centre", "beach": "Beachfront",
    "seaside": "Beachfront", "garden": "Garden Wing", "near the airport": "Airport Side",
    "near airport": "Airport Side", "airport side": "Airport Side",
}


def _to_int(token: str) -> Optional[int]:
    token = token.lower()
    if token in NUMBER_WORDS:
        return NUMBER_WORDS[token]
    return int(token) if token.isdigit() else None


def extract_budget(text: str) -> Optional[float]:
    t = text.lower()
    patterns = [
        r"(?:under|below|less than|cheaper than|at most|up to|max(?:imum)?(?: of)?|budget(?: of| is)?|within|around|about|no more than)\s*(?:usd|us)?\s*\$?\s*(\d+(?:\.\d+)?)(?!\d|-\d|\s*(?:guests?|people|persons?|adults?|nights?|pax|rooms?|km|pm|am))",
        r"\$\s*(\d+(?:\.\d+)?)",
        r"\b(\d+(?:\.\d+)?)\s*(?:dollars?|usd|bucks)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, t)
        if match:
            value = float(match.group(1))
            if 10 <= value <= 100000:
                return value
    return None


def extract_guests(text: str) -> Optional[int]:
    t = text.lower()
    match = re.search(r"\b" + _NUM + r"\s*(?:guests?|people|persons?|adults?|pax|travell?ers?)\b", t)
    if not match:
        match = re.search(r"\b(?:family|party|group) of " + _NUM + r"\b", t)
    if match:
        value = _to_int(match.group(1))
        if value and 1 <= value <= 20:
            return value
    return None


def extract_nights(text: str) -> Optional[int]:
    match = re.search(r"\b" + _NUM + r"[\s-]*nights?\b", text.lower())
    if match:
        value = _to_int(match.group(1))
        if value and 1 <= value <= 60:
            return value
    return None


def extract_dates(text: str, today: date) -> List[date]:
    t = text.lower()
    found = []  # (position, date)

    for m in re.finditer(r"\b(\d{4})-(\d{2})-(\d{2})\b", t):
        try:
            found.append((m.start(), date(int(m.group(1)), int(m.group(2)), int(m.group(3)))))
        except ValueError:
            pass

    def build(day, month, year_text):
        try:
            if year_text:
                return date(int(year_text), month, day)
            d = date(today.year, month, day)
            return d if d >= today else date(today.year + 1, month, day)
        except ValueError:
            return None

    for m in re.finditer(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(" + _MONTH_PAT + r")\b(?:,?\s+(\d{4}))?", t):
        d = build(int(m.group(1)), MONTHS[m.group(2)], m.group(3))
        if d:
            found.append((m.start(), d))
    for m in re.finditer(r"\b(" + _MONTH_PAT + r")\s+(\d{1,2})(?:st|nd|rd|th)?\b(?:,?\s+(\d{4}))?", t):
        d = build(int(m.group(2)), MONTHS[m.group(1)], m.group(3))
        if d:
            found.append((m.start(), d))

    for m in re.finditer(r"day after tomorrow|tomorrow|today|tonight", t):
        offset = {"day after tomorrow": 2, "tomorrow": 1}.get(m.group(0), 0)
        found.append((m.start(), today + timedelta(days=offset)))

    for m in re.finditer(r"\b(" + "|".join(WEEKDAYS) + r")\b", t):
        ahead = (WEEKDAYS.index(m.group(1)) - today.weekday()) % 7 or 7
        found.append((m.start(), today + timedelta(days=ahead)))

    found.sort(key=lambda item: item[0])
    unique: List[date] = []
    for _, d in found:
        if d not in unique:
            unique.append(d)
    return unique


def extract_entities(text: str, known_locations: Iterable[str] = (), known_types: Iterable[str] = (),
                     today: date = None) -> Dict:
    """Return only the details that were found in the message."""
    today = today or date.today()
    t = (text or "").lower()
    entities: Dict = {}

    for room_type in known_types:
        if re.search(r"\b" + re.escape(room_type.lower()) + r"s?\b", t):
            entities["room_type"] = room_type
            break

    known_locations = list(known_locations)
    for loc in known_locations:
        if loc.lower() in t:
            entities["location"] = loc
            break
    if "location" not in entities:
        for phrase, canonical in LOCATION_SYNONYMS.items():
            if phrase in t and canonical in known_locations:
                entities["location"] = canonical
                break

    budget = extract_budget(t)
    if budget:
        entities["budget"] = budget
    guests = extract_guests(t)
    if guests:
        entities["guests"] = guests

    dates = extract_dates(t, today)
    nights = extract_nights(t)
    if dates:
        entities["check_in"] = dates[0]
        if len(dates) > 1 and dates[1] > dates[0]:
            entities["check_out"] = dates[1]
        elif nights:
            entities["check_out"] = dates[0] + timedelta(days=nights)
    if nights:
        entities["nights"] = nights

    m = re.search(r"\broom\s*(?:no\.?|number|#)?\s*(\d{2,4})\b(?![-./]\d)", t)
    if m:
        entities["room_number"] = m.group(1)
    m = re.search(r"\bhb-?0*(\d+)\b", t) or re.search(
        r"\b(?:booking|reservation|ref|reference)\s*(?:id|number|no\.?|#)?\s*#?\s*0*(\d+)\b", t)
    if m:
        entities["booking_id"] = int(m.group(1))

    amenities: List[str] = []
    for key, canonical in AMENITY_SYNONYMS.items():
        if re.search(r"(?<![a-z])" + re.escape(key) + r"(?![a-z])", t) and canonical not in amenities:
            amenities.append(canonical)
    if amenities:
        entities["amenities"] = amenities
    return entities