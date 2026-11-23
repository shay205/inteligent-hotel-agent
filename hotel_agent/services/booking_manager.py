"""Bookings: availability checks, reservations, cancellations.

DOUBLE-BOOKING RULE
Two stays overlap when:   new_check_in < existing_check_out  AND  new_check_out > existing_check_in
(Check-out day is free for the next guest, so 10th-12th and 12th-14th do NOT overlap.)
The check and the insert happen inside ONE database transaction.
"""
import re
from datetime import date
from typing import Dict, List, Optional, Set

from hotel_agent.database.connection import Database
from hotel_agent.models.entities import Booking, Room, make_reference
from hotel_agent.services import validators as v
from hotel_agent.services.customer_manager import CustomerManager
from hotel_agent.services.room_manager import RoomManager


class BookingError(Exception):
    """A booking could not be created / changed (message is user friendly)."""


class RoomUnavailableError(BookingError):
    """The room is already booked for (part of) the requested dates."""


OVERLAP_SQL = (
    "SELECT COUNT(*) AS c FROM bookings "
    "WHERE room_id = ? AND status = 'Confirmed' AND check_in < ? AND check_out > ?"
)

_DETAIL_SELECT = """
    SELECT b.id AS booking_id, b.status, b.created_at, b.check_in, b.check_out, b.guests,
           b.total_price, b.notes,
           CAST(julianday(b.check_out) - julianday(b.check_in) AS INTEGER) AS nights,
           c.id AS customer_id, c.full_name AS customer, c.email, c.phone,
           r.id AS room_id, r.room_number, r.name AS room_name, r.accommodation_type,
           r.location, r.price_per_night, r.amenities
    FROM bookings b
    JOIN customers c ON c.id = b.customer_id
    JOIN rooms r ON r.id = b.room_id
"""


def parse_reference(text: str) -> Optional[int]:
    """'HB-00012' or '12' -> 12 (or None if it is not a reference)."""
    match = re.fullmatch(r"\s*(?:hb-?)?0*(\d+)\s*", str(text), flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


class BookingManager:
    def __init__(self, db: Database, rooms: RoomManager, customers: CustomerManager):
        self.db = db
        self.rooms = rooms
        self.customers = customers

    # ---------- availability ----------
    def is_available(self, room_id: int, check_in, check_out, exclude_booking_id: int = None) -> bool:
        ci, co = v.validate_stay_dates(check_in, check_out, allow_past=True)
        room = self.rooms.get_room(room_id)
        if room is None or not room.is_active:
            return False
        sql = OVERLAP_SQL
        params = [room_id, co.isoformat(), ci.isoformat()]
        if exclude_booking_id is not None:
            sql += " AND id != ?"
            params.append(exclude_booking_id)
        return self.db.query_one(sql, params)["c"] == 0

    def get_booked_room_ids(self, check_in, check_out) -> Set[int]:
        ci, co = v.validate_stay_dates(check_in, check_out, allow_past=True)
        rows = self.db.query(
            "SELECT DISTINCT room_id FROM bookings WHERE status = 'Confirmed' AND check_in < ? AND check_out > ?",
            (co.isoformat(), ci.isoformat()))
        return {r["room_id"] for r in rows}

    def get_available_rooms(self, check_in, check_out, guests: int = 1) -> List[Room]:
        booked = self.get_booked_room_ids(check_in, check_out)
        return [r for r in self.rooms.list_rooms(active_only=True)
                if r.id not in booked and r.capacity >= guests]

    # ---------- create / cancel ----------
    def create_booking(self, customer_id: int, room_id: int, check_in, check_out,
                       guests, notes: str = "") -> Booking:
        ci, co = v.validate_stay_dates(check_in, check_out, allow_past=False)
        guests = v.validate_guests(guests)
        notes = v.validate_optional_text(notes, "Notes", 300)
        if self.customers.get_customer(customer_id) is None:
            raise BookingError("Customer not found.")

        with self.db.transaction() as conn:
            room_row = conn.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
            if room_row is None or not room_row["is_active"]:
                raise BookingError("This room does not exist or is not open for booking.")
            if guests > room_row["capacity"]:
                raise BookingError(
                    f"Room {room_row['room_number']} sleeps at most {room_row['capacity']} guest(s).")
            clash = conn.execute(OVERLAP_SQL, (room_id, co.isoformat(), ci.isoformat())).fetchone()["c"]
            if clash:
                raise RoomUnavailableError(
                    f"Room {room_row['room_number']} is already booked for some of "
                    f"{ci.isoformat()} to {co.isoformat()}.")
            total = round((co - ci).days * float(room_row["price_per_night"]), 2)
            cursor = conn.execute(
                """INSERT INTO bookings (customer_id, room_id, check_in, check_out, guests,
                                         total_price, status, notes)
                   VALUES (?, ?, ?, ?, ?, ?, 'Confirmed', ?)""",
                (customer_id, room_id, ci.isoformat(), co.isoformat(), guests, total, notes))
            booking_id = cursor.lastrowid
        return self.get_booking(booking_id)

    def book_for_guest(self, full_name, email, phone, room_id: int, check_in, check_out,
                       guests, notes: str = "") -> Booking:
        """Convenience used by the UI: create/find the customer, then book."""
        customer = self.customers.get_or_create(full_name, email, phone)
        return self.create_booking(customer.id, room_id, check_in, check_out, guests, notes)

    def cancel_booking(self, booking_id: int) -> Booking:
        booking = self.get_booking(booking_id)
        if booking is None:
            raise BookingError("Booking not found.")
        if booking.status == "Cancelled":
            raise BookingError(f"Booking {booking.reference} is already cancelled.")
        with self.db.transaction() as conn:
            conn.execute("UPDATE bookings SET status = 'Cancelled' WHERE id = ?", (booking_id,))
            conn.execute("UPDATE service_orders SET status = 'Cancelled' WHERE booking_id = ?", (booking_id,))
        return self.get_booking(booking_id)

    # ---------- read ----------
    def get_booking(self, booking_id: int) -> Optional[Booking]:
        row = self.db.query_one("SELECT * FROM bookings WHERE id = ?", (booking_id,))
        return Booking.from_row(row) if row else None

    def get_booking_details(self, booking_id: int) -> Optional[Dict]:
        row = self.db.query_one(_DETAIL_SELECT + " WHERE b.id = ?", (booking_id,))
        if row is None:
            return None
        row["id"] = row["booking_id"]
        row["reference"] = make_reference(row["booking_id"])
        return row

    def list_bookings(self, status: str = None, limit: int = None) -> List[Dict]:
        sql = _DETAIL_SELECT
        params: list = []
        if status:
            sql += " WHERE b.status = ?"
            params.append(status)
        sql += " ORDER BY b.id DESC"
        if limit:
            sql += f" LIMIT {int(limit)}"
        rows = self.db.query(sql, params)
        for row in rows:
            row["id"] = row["booking_id"]
            row["reference"] = make_reference(row["booking_id"])
        return rows