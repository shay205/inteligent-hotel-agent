import unittest

from hotel_agent.services.validators import ValidationError
from tests.helpers import HotelTestCase


class AvailabilityTests(HotelTestCase):
    def test_free_room_is_available(self):
        self.assertTrue(self.ctx.bookings.is_available(self.r_std, self.d(0), self.d(2)))

    def test_booked_room_is_unavailable_for_overlap(self):
        self.make_booking(self.r_std, 0, 3)
        self.assertFalse(self.ctx.bookings.is_available(self.r_std, self.d(1), self.d(2)))
        self.assertFalse(self.ctx.bookings.is_available(self.r_std, self.d(2), self.d(5)))
        self.assertFalse(self.ctx.bookings.is_available(self.r_std, self.d(-2), self.d(1)))

    def test_back_to_back_stays_are_allowed(self):
        self.make_booking(self.r_std, 0, 3)
        self.assertTrue(self.ctx.bookings.is_available(self.r_std, self.d(3), self.d(5)))
        self.assertTrue(self.ctx.bookings.is_available(self.r_std, self.d(-2), self.d(0)))

    def test_cancelled_booking_frees_the_room(self):
        booking = self.make_booking(self.r_std, 0, 3)
        self.ctx.bookings.cancel_booking(booking.id)
        self.assertTrue(self.ctx.bookings.is_available(self.r_std, self.d(0), self.d(3)))

    def test_available_rooms_respect_guest_count_and_bookings(self):
        self.make_booking(self.r_fam, 0, 2)
        rooms = {r.room_number for r in self.ctx.bookings.get_available_rooms(self.d(0), self.d(2), guests=4)}
        self.assertEqual(rooms, {"X1"})

    def test_inactive_room_is_not_available(self):
        self.ctx.rooms.update_room(self.r_std, is_active=False)
        self.assertFalse(self.ctx.bookings.is_available(self.r_std, self.d(0), self.d(1)))

    def test_invalid_dates_rejected(self):
        with self.assertRaises(ValidationError):
            self.ctx.bookings.is_available(self.r_std, self.d(3), self.d(1))


if __name__ == "__main__":
    unittest.main()