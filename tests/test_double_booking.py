import threading
import unittest

from hotel_agent.services.booking_manager import RoomUnavailableError
from tests.helpers import HotelTestCase


class DoubleBookingTests(HotelTestCase):
    def test_exact_same_dates_rejected(self):
        self.make_booking(self.r_std, 0, 3)
        with self.assertRaises(RoomUnavailableError):
            self.make_booking(self.r_std, 0, 3, email="other@example.com")

    def test_partial_overlaps_rejected(self):
        self.make_booking(self.r_std, 2, 6)
        for a, b in [(0, 3), (5, 8), (3, 5), (0, 10)]:
            with self.assertRaises(RoomUnavailableError):
                self.make_booking(self.r_std, a, b, email="other@example.com")

    def test_adjacent_stays_and_other_rooms_allowed(self):
        self.make_booking(self.r_std, 2, 6)
        self.make_booking(self.r_std, 6, 8, email="b@example.com")
        self.make_booking(self.r_std, 0, 2, email="c@example.com")
        self.make_booking(self.r_dlx_city, 2, 6, email="d@example.com")

    def test_rebooking_allowed_after_cancellation(self):
        first = self.make_booking(self.r_std, 0, 3)
        self.ctx.bookings.cancel_booking(first.id)
        self.make_booking(self.r_std, 0, 3, email="other@example.com")

    def test_only_one_of_many_simultaneous_bookings_succeeds(self):
        outcomes = []

        def attempt(i):
            try:
                self.make_booking(self.r_suite, 0, 2, email=f"user{i}@example.com")
                outcomes.append("ok")
            except RoomUnavailableError:
                outcomes.append("blocked")

        threads = [threading.Thread(target=attempt, args=(i,)) for i in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(outcomes.count("ok"), 1)
        self.assertEqual(outcomes.count("blocked"), 5)


if __name__ == "__main__":
    unittest.main()