"""Additional hotel services (room service, spa, airport transfer, ...) and orders."""
import sqlite3
from typing import Dict, List, Optional

from hotel_agent.database.connection import Database
from hotel_agent.models.entities import Service
from hotel_agent.services import validators as v


class ServiceError(Exception):
    pass


class ServiceManager:
    def __init__(self, db: Database):
        self.db = db

    def add_service(self, name, category, price, description="") -> int:
        name = v.validate_required_text(name, "Service name", 60)
        category = v.validate_required_text(category, "Category", 30)
        price = v.validate_non_negative_price(price, "Service price")
        description = v.validate_optional_text(description, "Description", 300)
        try:
            return self.db.execute(
                "INSERT INTO services (name, category, price, description, is_active) VALUES (?, ?, ?, ?, 1)",
                (name, category, price, description))
        except sqlite3.IntegrityError:
            raise ServiceError(f"A service called '{name}' already exists.")

    def set_active(self, service_id: int, active: bool) -> None:
        self.db.execute("UPDATE services SET is_active = ? WHERE id = ?", (1 if active else 0, service_id))

    def get_service(self, service_id: int) -> Optional[Service]:
        row = self.db.query_one("SELECT * FROM services WHERE id = ?", (service_id,))
        return Service.from_row(row) if row else None

    def list_services(self, active_only: bool = True) -> List[Service]:
        sql = "SELECT * FROM services"
        if active_only:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY category, price"
        return [Service.from_row(r) for r in self.db.query(sql)]

    def order_service(self, booking_id: int, service_id: int, quantity=1, details: str = "") -> int:
        qty = v.validate_quantity(quantity)
        details = v.validate_optional_text(details, "Details", 200)
        booking = self.db.query_one("SELECT id, status FROM bookings WHERE id = ?", (booking_id,))
        if booking is None:
            raise ServiceError("Booking not found.")
        if booking["status"] != "Confirmed":
            raise ServiceError("Services can only be ordered for confirmed bookings.")
        service = self.get_service(service_id)
        if service is None or not service.is_active:
            raise ServiceError("This service is not available.")
        return self.db.execute(
            """INSERT INTO service_orders (booking_id, service_id, quantity, total_price, details, status)
               VALUES (?, ?, ?, ?, ?, 'Requested')""",
            (booking_id, service_id, qty, round(service.price * qty, 2), details))

    def list_orders(self, booking_id: int = None) -> List[Dict]:
        sql = """SELECT so.id, so.booking_id, s.name AS service, s.category, so.quantity,
                        so.total_price, so.details, so.status, so.created_at
                 FROM service_orders so JOIN services s ON s.id = so.service_id"""
        params: list = []
        if booking_id is not None:
            sql += " WHERE so.booking_id = ?"
            params.append(booking_id)
        sql += " ORDER BY so.id DESC"
        return self.db.query(sql, params)

    def cancel_order(self, order_id: int) -> None:
        row = self.db.query_one("SELECT status FROM service_orders WHERE id = ?", (order_id,))
        if row is None:
            raise ServiceError("Order not found.")
        if row["status"] == "Cancelled":
            raise ServiceError("This order is already cancelled.")
        self.db.execute("UPDATE service_orders SET status = 'Cancelled' WHERE id = ?", (order_id,))