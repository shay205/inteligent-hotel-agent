"""Room management: add, edit, delete, list and show availability."""
import sqlite3
from datetime import date
from typing import Dict, List, Optional

from hotel_agent.database.connection import Database
from hotel_agent.models.entities import Room
from hotel_agent.services import validators as v


class RoomError(Exception):
    """Raised for room-related business rule problems."""


_FIELD_VALIDATORS = {
    "room_number": v.validate_room_number,
    "name": lambda x: v.validate_required_text(x, "Room name", 60),
    "accommodation_type": v.validate_accommodation_type,
    "location": lambda x: v.validate_required_text(x, "Location", 50),
    "price_per_night": v.validate_price,
    "capacity": v.validate_capacity,
    "amenities": v.normalize_amenities,
    "description": lambda x: v.validate_optional_text(x, "Description", 300),
}


class RoomManager:
    def __init__(self, db: Database):
        self.db = db

    # ---------- create / update / delete ----------
    def add_room(self, room_number, name, accommodation_type, location,
                 price_per_night, capacity, amenities="", description="") -> int:
        data = {
            "room_number": room_number, "name": name,
            "accommodation_type": accommodation_type, "location": location,
            "price_per_night": price_per_night, "capacity": capacity,
            "amenities": amenities, "description": description,
        }
        clean = {key: _FIELD_VALIDATORS[key](value) for key, value in data.items()}
        try:
            return self.db.execute(
                """INSERT INTO rooms (room_number, name, accommodation_type, location,
                       price_per_night, capacity, amenities, description, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                (clean["room_number"], clean["name"], clean["accommodation_type"],
                 clean["location"], clean["price_per_night"], clean["capacity"],
                 clean["amenities"], clean["description"]),
            )
        except sqlite3.IntegrityError:
            raise RoomError(f"Room number {clean['room_number']} already exists.")

    def update_room(self, room_id: int, **fields) -> None:
        if self.get_room(room_id) is None:
            raise RoomError("Room not found.")
        updates, params = [], []
        for key, value in fields.items():
            if key == "is_active":
                updates.append("is_active = ?")
                params.append(1 if value else 0)
            elif key in _FIELD_VALIDATORS:
                updates.append(f"{key} = ?")
                params.append(_FIELD_VALIDATORS[key](value))
            else:
                raise RoomError(f"Unknown room field: {key}")
        if not updates:
            return
        params.append(room_id)
        try:
            self.db.execute(f"UPDATE rooms SET {', '.join(updates)} WHERE id = ?", params)
        except sqlite3.IntegrityError:
            raise RoomError("That room number is already used by another room.")

    def delete_room(self, room_id: int) -> None:
        if self.get_room(room_id) is None:
            raise RoomError("Room not found.")
        count = self.db.query_one("SELECT COUNT(*) AS c FROM bookings WHERE room_id = ?", (room_id,))["c"]
        if count:
            raise RoomError(
                f"This room has {count} booking record(s) and cannot be deleted. "
                "Deactivate it instead (Edit Room -> untick 'Room is active')."
            )
        self.db.execute("DELETE FROM rooms WHERE id = ?", (room_id,))

    # ---------- queries ----------
    def get_room(self, room_id: int) -> Optional[Room]:
        row = self.db.query_one("SELECT * FROM rooms WHERE id = ?", (room_id,))
        return Room.from_row(row) if row else None

    def get_by_number(self, room_number: str) -> Optional[Room]:
        row = self.db.query_one("SELECT * FROM rooms WHERE room_number = ?", (str(room_number),))
        return Room.from_row(row) if row else None

    def list_rooms(self, active_only: bool = False) -> List[Room]:
        sql = "SELECT * FROM rooms"
        if active_only:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY room_number"
        return [Room.from_row(r) for r in self.db.query(sql)]

    def get_locations(self) -> List[str]:
        rows = self.db.query("SELECT DISTINCT location FROM rooms WHERE is_active = 1 ORDER BY location")
        return [r["location"] for r in rows]

    def get_types(self) -> List[str]:
        rows = self.db.query("SELECT DISTINCT accommodation_type FROM rooms WHERE is_active = 1 ORDER BY accommodation_type")
        return [r["accommodation_type"] for r in rows]

    def availability_table(self, on_date: date) -> List[Dict]:
        """Status of every room on one date (Available / Occupied / Inactive)."""
        day = on_date.isoformat()
        rows = self.db.query(
            """SELECT r.*, b.id AS booking_id, b.check_out AS occupied_until, c.full_name AS guest
               FROM rooms r
               LEFT JOIN bookings b ON b.room_id = r.id AND b.status = 'Confirmed'
                    AND b.check_in <= ? AND b.check_out > ?
               LEFT JOIN customers c ON c.id = b.customer_id
               ORDER BY r.room_number""",
            (day, day),
        )
        table = []
        for r in rows:
            if not r["is_active"]:
                status = "Inactive"
            elif r["booking_id"]:
                status = "Occupied"
            else:
                status = "Available"
            table.append({
                "Room": r["room_number"], "Name": r["name"], "Type": r["accommodation_type"],
                "Location": r["location"], "Price/night": r["price_per_night"],
                "Capacity": r["capacity"], "Status": status,
                "Guest": r["guest"] or "", "Occupied until": r["occupied_until"] or "",
            })
        return table