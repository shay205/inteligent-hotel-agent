"""Input validation. Every function either returns a clean value or raises ValidationError."""
import re
from datetime import date, datetime
from typing import Iterable, List, Tuple, Union

from hotel_agent.config import ACCOMMODATION_TYPES, MAX_GUESTS, MAX_STAY_NIGHTS


class ValidationError(ValueError):
    """Raised when user input is not acceptable. The message is safe to show to the user."""


EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^\+?[0-9][0-9\s\-()]{5,19}$")
ROOM_NUMBER_RE = re.compile(r"^[A-Za-z0-9\-]{1,10}$")


def parse_date(value: Union[str, date, datetime], field: str = "Date") -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            pass
    raise ValidationError(f"{field} is not a valid date (use YYYY-MM-DD).")


def validate_stay_dates(check_in, check_out, allow_past: bool = False) -> Tuple[date, date]:
    ci = parse_date(check_in, "Check-in date")
    co = parse_date(check_out, "Check-out date")
    if co <= ci:
        raise ValidationError("Check-out date must be after the check-in date.")
    if not allow_past and ci < date.today():
        raise ValidationError("Check-in date cannot be in the past.")
    if (co - ci).days > MAX_STAY_NIGHTS:
        raise ValidationError(f"A stay cannot be longer than {MAX_STAY_NIGHTS} nights.")
    return ci, co


def validate_guests(value, capacity: int = None) -> int:
    try:
        guests = int(value)
    except (TypeError, ValueError):
        raise ValidationError("Number of guests must be a whole number.")
    if guests < 1:
        raise ValidationError("At least 1 guest is required.")
    if guests > MAX_GUESTS:
        raise ValidationError(f"A single booking cannot exceed {MAX_GUESTS} guests.")
    if capacity is not None and guests > capacity:
        raise ValidationError(f"This room sleeps at most {capacity} guest(s); you entered {guests}.")
    return guests


def validate_required_text(value, field: str, max_len: int = 100, min_len: int = 1) -> str:
    text = (value or "").strip() if isinstance(value, str) or value is None else str(value).strip()
    if len(text) < min_len:
        raise ValidationError(f"{field} is required." if min_len <= 1 else f"{field} must be at least {min_len} characters.")
    if len(text) > max_len:
        raise ValidationError(f"{field} must be at most {max_len} characters.")
    return text


def validate_optional_text(value, field: str, max_len: int = 300) -> str:
    text = (value or "").strip() if isinstance(value, str) or value is None else str(value).strip()
    if len(text) > max_len:
        raise ValidationError(f"{field} must be at most {max_len} characters.")
    return text


def validate_name(value) -> str:
    name = validate_required_text(value, "Full name", 100, 2)
    if re.search(r"[0-9<>@#$%^*_=+{}\[\]|\\/]", name):
        raise ValidationError("Full name contains invalid characters.")
    return name


def validate_email(value) -> str:
    email = validate_required_text(value, "Email", 120).lower()
    if not EMAIL_RE.match(email):
        raise ValidationError("Please enter a valid email address, e.g. name@example.com.")
    return email


def validate_phone(value) -> str:
    phone = validate_required_text(value, "Phone number", 25)
    if not PHONE_RE.match(phone):
        raise ValidationError("Please enter a valid phone number (digits, spaces, +, -, brackets).")
    return phone


def validate_price(value, field: str = "Price per night") -> float:
    try:
        price = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} must be a number.")
    if price <= 0:
        raise ValidationError(f"{field} must be greater than zero.")
    if price > 100000:
        raise ValidationError(f"{field} is unrealistically high.")
    return round(price, 2)


def validate_non_negative_price(value, field: str = "Price") -> float:
    try:
        price = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} must be a number.")
    if price < 0 or price > 100000:
        raise ValidationError(f"{field} must be between 0 and 100000.")
    return round(price, 2)


def validate_capacity(value) -> int:
    try:
        cap = int(value)
    except (TypeError, ValueError):
        raise ValidationError("Capacity must be a whole number.")
    if cap < 1 or cap > MAX_GUESTS:
        raise ValidationError(f"Capacity must be between 1 and {MAX_GUESTS}.")
    return cap


def validate_room_number(value) -> str:
    number = validate_required_text(value, "Room number", 10)
    if not ROOM_NUMBER_RE.match(number):
        raise ValidationError("Room number may only contain letters, digits and hyphens (max 10).")
    return number


def validate_accommodation_type(value) -> str:
    text = validate_required_text(value, "Accommodation type", 30)
    for allowed in ACCOMMODATION_TYPES:
        if allowed.lower() == text.lower():
            return allowed
    raise ValidationError(f"Accommodation type must be one of: {', '.join(ACCOMMODATION_TYPES)}.")


def normalize_amenities(value: Union[str, Iterable[str], None]) -> str:
    if value is None:
        return ""
    items: List[str] = value.split(",") if isinstance(value, str) else list(value)
    cleaned = []
    for item in items:
        item = str(item).strip()
        if item and item.lower() not in [c.lower() for c in cleaned]:
            cleaned.append(item)
    text = ", ".join(cleaned)
    if len(text) > 300:
        raise ValidationError("Amenities list is too long.")
    return text


def validate_quantity(value, field: str = "Quantity") -> int:
    try:
        qty = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} must be a whole number.")
    if qty < 1 or qty > 50:
        raise ValidationError(f"{field} must be between 1 and 50.")
    return qty