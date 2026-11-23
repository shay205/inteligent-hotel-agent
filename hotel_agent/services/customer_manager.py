"""Customer records (created automatically when a booking is made)."""
from typing import Dict, List, Optional

from hotel_agent.database.connection import Database
from hotel_agent.models.entities import Customer
from hotel_agent.services import validators as v


class CustomerManager:
    def __init__(self, db: Database):
        self.db = db

    def get_or_create(self, full_name, email, phone) -> Customer:
        """Find a customer by email, or create one. Details are validated first."""
        name = v.validate_name(full_name)
        email = v.validate_email(email)
        phone = v.validate_phone(phone)
        existing = self.db.query_one("SELECT * FROM customers WHERE email = ?", (email,))
        if existing:
            self.db.execute("UPDATE customers SET full_name = ?, phone = ? WHERE id = ?",
                            (name, phone, existing["id"]))
            return self.get_customer(existing["id"])
        new_id = self.db.execute(
            "INSERT INTO customers (full_name, email, phone) VALUES (?, ?, ?)", (name, email, phone))
        return self.get_customer(new_id)

    def get_customer(self, customer_id: int) -> Optional[Customer]:
        row = self.db.query_one("SELECT * FROM customers WHERE id = ?", (customer_id,))
        return Customer.from_row(row) if row else None

    def list_customers(self) -> List[Dict]:
        return self.db.query("SELECT * FROM customers ORDER BY full_name")