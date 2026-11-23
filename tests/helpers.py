"""Shared test setup: a fresh temporary database with a small, predictable set of rooms."""
import os
import shutil
import tempfile
import unittest
from datetime import date, timedelta

from hotel_agent.app_context import build_context


class HotelTestCase(unittest.TestCase):
    """Base class: every test gets its own empty database and 5 known rooms."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ctx = build_context(os.path.join(self.tmp, "test.db"), seed=False)
        rooms = self.ctx.rooms
        self.r_std = rooms.add_room("S1", "City Standard", "Standard", "City Centre", 60, 2, "WiFi, TV")
        self.r_dlx_city = rooms.add_room("D1", "City Deluxe", "Deluxe", "City Centre", 110, 3, "WiFi, TV, Balcony")
        self.r_dlx_beach = rooms.add_room("D2", "Beach Deluxe", "Deluxe", "Beachfront", 140, 3, "WiFi, Sea View, Balcony")
        self.r_fam = rooms.add_room("F1", "Family Room", "Family", "Garden Wing", 150, 5, "WiFi, Kitchenette, Pool Access")
        self.r_suite = rooms.add_room("X1", "Beach Suite", "Suite", "Beachfront", 320, 4, "WiFi, Sea View, Bathtub, Lounge Access")
        for name, cat, price in [("Relaxation Massage", "Spa", 70), ("Airport Transfer", "Airport Transfer", 35),
                                 ("Kids Club", "Childcare", 30), ("Dinner Table", "Restaurant", 25),
                                 ("Business Pack", "Business", 25), ("Laundry", "Laundry", 20)]:
            self.ctx.services.add_service(name, cat, price, "test service")
        self.start = date.today() + timedelta(days=30)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def d(self, offset: int) -> date:
        """A date `offset` days after the base test date."""
        return self.start + timedelta(days=offset)

    def make_booking(self, room_id, in_offset, out_offset, guests=1, email="guest@example.com"):
        return self.ctx.bookings.book_for_guest("Test Guest", email, "+254700000000", room_id,
                                                self.d(in_offset), self.d(out_offset), guests)