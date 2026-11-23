import os
import unittest
from datetime import date, timedelta

from hotel_agent.app_context import build_context
from hotel_agent.services.booking_manager import BookingError
from hotel_agent.services.validators import ValidationError
from tests.helpers import HotelTestCase


class BookingTests(HotelTestCase):
    def test_create_booking_calculates_total(self):
        b = self.make_booking(self.r_dlx_city, 0, 3, guests=2)
        self.assertEqual(b.total_price, 330.0)
        self.assertEqual(b.status, "Confirmed")
        self.assertEqual(b.nights, 3)
        self.assertEqual(b.reference, f"HB-{b.id:05d}")

    def test_booking_details_include_guest_and_room(self):
        b = self.make_booking(self.r_std, 0, 1)
        details = self.ctx.bookings.get_booking_details(b.id)
        self.assertEqual(details["customer"], "Test Guest")
        self.assertEqual(details["room_number"], "S1")

    def test_too_many_guests_rejected(self):
        with self.assertRaises(BookingError):
            self.make_booking(self.r_std, 0, 1, guests=5)

    def test_past_dates_rejected(self):
        with self.assertRaises(ValidationError):
            self.ctx.bookings.book_for_guest("Test Guest", "a@example.com", "+254700000000", self.r_std,
                                             date.today() - timedelta(days=2), date.today() + timedelta(days=1), 1)

    def test_invalid_customer_input_rejected(self):
        for name, email, phone in [("", "a@example.com", "+254700000000"), ("Bob", "not-an-email", "+254700000000"),
                                   ("Bob", "a@example.com", "abc")]:
            with self.assertRaises(ValidationError):
                self.ctx.bookings.book_for_guest(name, email, phone, self.r_std, self.d(0), self.d(1), 1)

    def test_cancel_booking(self):
        b = self.make_booking(self.r_std, 0, 2)
        self.assertEqual(self.ctx.bookings.cancel_booking(b.id).status, "Cancelled")
        with self.assertRaises(BookingError):
            self.ctx.bookings.cancel_booking(b.id)

    def test_same_customer_reused_by_email(self):
        self.make_booking(self.r_std, 0, 1)
        self.make_booking(self.r_dlx_city, 0, 1)
        self.assertEqual(len(self.ctx.customers.list_customers()), 1)

    def test_bookings_persist_after_reopening_database(self):
        b = self.make_booking(self.r_std, 0, 2)
        reopened = build_context(os.path.join(self.tmp, "test.db"), seed=False)
        self.assertIsNotNone(reopened.bookings.get_booking(b.id))

    def test_service_order_requires_confirmed_booking(self):
        b = self.make_booking(self.r_std, 0, 2)
        service = self.ctx.services.list_services()[0]
        order_id = self.ctx.services.order_service(b.id, service.id, 2)
        self.assertTrue(order_id)
        self.ctx.bookings.cancel_booking(b.id)
        self.assertEqual(self.ctx.services.list_orders(b.id)[0]["status"], "Cancelled")


if __name__ == "__main__":
    unittest.main()