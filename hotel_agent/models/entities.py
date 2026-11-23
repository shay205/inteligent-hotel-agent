"""Plain data classes shared by every layer of the application."""
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional


def split_amenities(text) -> List[str]:
    return [a.strip() for a in (text or "").split(",") if a.strip()]


@dataclass
class Room:
    id: Optional[int]
    room_number: str
    name: str
    accommodation_type: str
    location: str
    price_per_night: float
    capacity: int
    amenities: List[str] = field(default_factory=list)
    description: str = ""
    is_active: bool = True

    @classmethod
    def from_row(cls, row) -> "Room":
        return cls(
            id=row["id"],
            room_number=row["room_number"],
            name=row["name"],
            accommodation_type=row["accommodation_type"],
            location=row["location"],
            price_per_night=float(row["price_per_night"]),
            capacity=int(row["capacity"]),
            amenities=split_amenities(row["amenities"]),
            description=row["description"] or "",
            is_active=bool(row["is_active"]),
        )

    @property
    def amenities_text(self) -> str:
        return ", ".join(self.amenities)

    @property
    def label(self) -> str:
        return f"Room {self.room_number} - {self.name} ({self.accommodation_type})"


@dataclass
class Customer:
    id: Optional[int]
    full_name: str
    email: str
    phone: str
    created_at: str = ""

    @classmethod
    def from_row(cls, row) -> "Customer":
        return cls(row["id"], row["full_name"], row["email"], row["phone"], row["created_at"])


@dataclass
class Booking:
    id: Optional[int]
    customer_id: int
    room_id: int
    check_in: date
    check_out: date
    guests: int
    total_price: float
    status: str = "Confirmed"
    created_at: str = ""
    notes: str = ""

    @classmethod
    def from_row(cls, row) -> "Booking":
        return cls(
            id=row["id"],
            customer_id=row["customer_id"],
            room_id=row["room_id"],
            check_in=date.fromisoformat(row["check_in"]),
            check_out=date.fromisoformat(row["check_out"]),
            guests=row["guests"],
            total_price=float(row["total_price"]),
            status=row["status"],
            created_at=row["created_at"],
            notes=row["notes"] or "",
        )

    @property
    def reference(self) -> str:
        return make_reference(self.id)

    @property
    def nights(self) -> int:
        return (self.check_out - self.check_in).days


def make_reference(booking_id) -> str:
    """Human friendly booking reference, e.g. 12 -> HB-00012."""
    return f"HB-{int(booking_id):05d}"


@dataclass
class Service:
    id: Optional[int]
    name: str
    category: str
    price: float
    description: str = ""
    is_active: bool = True

    @classmethod
    def from_row(cls, row) -> "Service":
        return cls(row["id"], row["name"], row["category"], float(row["price"]),
                   row["description"] or "", bool(row["is_active"]))


@dataclass
class Preferences:
    """What the customer is looking for. Every field is optional except guests."""
    location: Optional[str] = None
    budget: Optional[float] = None          # maximum price per night
    accommodation_type: Optional[str] = None
    check_in: Optional[date] = None
    check_out: Optional[date] = None
    guests: int = 1
    amenities: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)

    @property
    def has_dates(self) -> bool:
        return self.check_in is not None and self.check_out is not None

    @property
    def nights(self) -> int:
        return (self.check_out - self.check_in).days if self.has_dates else 0

    def to_dict(self) -> Dict:
        return {
            "location": self.location, "budget": self.budget,
            "accommodation_type": self.accommodation_type,
            "check_in": str(self.check_in) if self.check_in else None,
            "check_out": str(self.check_out) if self.check_out else None,
            "guests": self.guests, "amenities": list(self.amenities),
            "interests": list(self.interests),
        }