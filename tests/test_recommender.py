import unittest

from hotel_agent.models.entities import Preferences
from tests.helpers import HotelTestCase


class RecommenderTests(HotelTestCase):
    def test_best_match_is_ranked_first_and_scores_sorted(self):
        prefs = Preferences(location="Beachfront", budget=150, accommodation_type="Deluxe",
                            check_in=self.d(0), check_out=self.d(2), guests=2)
        recs = self.ctx.recommender.recommend(prefs)
        self.assertEqual(recs[0].room.room_number, "D2")
        scores = [r.score for r in recs]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_reasons_are_provided(self):
        prefs = Preferences(location="Beachfront", budget=150, accommodation_type="Deluxe", guests=2)
        rec = self.ctx.recommender.recommend(prefs)[0]
        self.assertTrue(rec.reasons)
        self.assertTrue(any("Beachfront" in r for r in rec.reasons))

    def test_rooms_that_are_too_small_are_excluded(self):
        prefs = Preferences(guests=4)
        numbers = {r.room.room_number for r in self.ctx.recommender.recommend(prefs)}
        self.assertEqual(numbers, {"F1", "X1"})

    def test_over_budget_room_scores_lower(self):
        prefs = Preferences(budget=100, accommodation_type="Deluxe", guests=2)
        rec = {r.room.room_number: r for r in self.ctx.recommender.recommend(prefs, min_score=0)}
        self.assertGreater(rec["D1"].score, rec["D2"].score)
        self.assertTrue(rec["D2"].warnings)

    def test_amenity_preference_changes_score(self):
        with_pref = Preferences(guests=2, amenities=["Sea View"])
        rec = {r.room.room_number: r for r in self.ctx.recommender.recommend(with_pref, min_score=0)}
        self.assertGreater(rec["D2"].score, rec["D1"].score)

    def test_booked_room_not_recommended_but_flagged_when_requested(self):
        self.make_booking(self.r_dlx_beach, 0, 3)
        prefs = Preferences(location="Beachfront", accommodation_type="Deluxe",
                            check_in=self.d(1), check_out=self.d(2), guests=2)
        normal = [r.room.room_number for r in self.ctx.recommender.recommend(prefs)]
        self.assertNotIn("D2", normal)
        flagged = {r.room.room_number: r for r in self.ctx.recommender.recommend(prefs, include_unavailable=True)}
        self.assertFalse(flagged["D2"].available)

    def test_alternatives_when_preferred_room_unavailable(self):
        self.make_booking(self.r_dlx_beach, 0, 3)
        prefs = Preferences(check_in=self.d(0), check_out=self.d(3), guests=2)
        alts = self.ctx.recommender.find_alternatives(self.r_dlx_beach, prefs)
        self.assertTrue(alts)
        self.assertNotIn("D2", [a.room.room_number for a in alts])
        self.assertTrue(all(a.available for a in alts))

    def test_fallback_relaxes_preferences_when_nothing_scores_well(self):
        for room_id in (self.r_std, self.r_dlx_city, self.r_dlx_beach, self.r_suite):
            self.make_booking(room_id, 0, 3, guests=1, email=f"u{room_id}@example.com")
        prefs = Preferences(location="Beachfront", accommodation_type="Suite", budget=100,
                            check_in=self.d(0), check_out=self.d(3), guests=2, amenities=["Sea View"])
        self.assertEqual(self.ctx.recommender.recommend(prefs), [])
        recs, note = self.ctx.recommender.recommend_with_fallback(prefs)
        self.assertEqual([r.room.room_number for r in recs], ["F1"])
        self.assertIn("location", note)

    def test_no_rooms_at_all_gives_clear_message(self):
        for room_id in (self.r_std, self.r_dlx_city, self.r_dlx_beach, self.r_fam, self.r_suite):
            self.make_booking(room_id, 0, 3, guests=1, email=f"u{room_id}@example.com")
        prefs = Preferences(check_in=self.d(0), check_out=self.d(3), guests=1)
        recs, note = self.ctx.recommender.recommend_with_fallback(prefs)
        self.assertEqual(recs, [])
        self.assertIn("No rooms are available", note)


if __name__ == "__main__":
    unittest.main()