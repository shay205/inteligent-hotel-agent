import unittest

from hotel_agent.ai.service_recommender import extract_interests
from hotel_agent.models.entities import Preferences
from tests.helpers import HotelTestCase


class ServiceRecommenderTests(HotelTestCase):
    def categories(self, prefs, n=6):
        return [s.service.category for s in self.ctx.service_recommender.recommend(prefs, n)]

    def test_relaxation_suggests_spa(self):
        self.assertEqual(self.categories(Preferences(interests=["relaxation"]))[0], "Spa")

    def test_family_suggests_childcare(self):
        self.assertIn("Childcare", self.categories(Preferences(guests=4, accommodation_type="Family")))

    def test_airport_location_suggests_transfer(self):
        self.assertEqual(self.categories(Preferences(location="Airport Side"))[0], "Airport Transfer")

    def test_business_executive_suggests_business_pack(self):
        self.assertIn("Business", self.categories(Preferences(accommodation_type="Executive", interests=["business"])))

    def test_romantic_suggests_restaurant(self):
        self.assertIn("Restaurant", self.categories(Preferences(interests=["romantic"])))

    def test_long_stay_suggests_laundry(self):
        from datetime import date, timedelta
        prefs = Preferences(check_in=date.today(), check_out=date.today() + timedelta(days=6))
        self.assertIn("Laundry", self.categories(prefs))

    def test_default_suggestions_when_no_preferences(self):
        self.assertTrue(self.ctx.service_recommender.recommend(Preferences()))

    def test_interest_extraction_from_text(self):
        self.assertIn("relaxation", extract_interests("I would love a massage"))
        self.assertIn("family", extract_interests("travelling with my kids"))


if __name__ == "__main__":
    unittest.main()