import unittest
from datetime import date

from hotel_agent.ai.nlp.entity_extractor import extract_entities
from hotel_agent.ai.nlp.intent_classifier import IntentClassifier
from hotel_agent.ai.nlp.preprocessing import clean_text, preprocess
from tests.helpers import HotelTestCase


class IntentTests(unittest.TestCase):
    def setUp(self):
        self.clf = IntentClassifier()

    def test_intents(self):
        cases = {
            "How much is a deluxe room per night?": "PRICE",
            "What is the price of a suite?": "PRICE",
            "Is there a room available tomorrow?": "AVAILABILITY",
            "Do you have any vacancy this weekend?": "AVAILABILITY",
            "Does the room have wifi and a pool?": "FACILITIES",
            "I want to book a room": "BOOKING",
            "How do I make a reservation?": "BOOKING",
            "Cancel my booking please": "CANCELLATION",
            "Do you have a spa or airport shuttle?": "SERVICES",
            "Can I order room service?": "SERVICES",
            "Recommend a room for two guests": "RECOMMENDATION",
            "What time is check-in?": "CHECKIN_INFO",
            "Hello there": "GREETING",
            "Thanks a lot": "THANKS",
            "Goodbye": "GOODBYE",
        }
        for message, expected in cases.items():
            self.assertEqual(self.clf.classify(message).intent, expected, message)

    def test_unknown_and_empty(self):
        self.assertEqual(self.clf.classify("zzzz qqqq").intent, "UNKNOWN")
        self.assertEqual(self.clf.classify("").intent, "UNKNOWN")
        self.assertEqual(self.clf.classify(None).intent, "UNKNOWN")

    def test_case_and_punctuation_are_ignored(self):
        self.assertEqual(self.clf.classify("HOW MUCH?!?! is it").intent, "PRICE")

    def test_preprocessing(self):
        self.assertEqual(clean_text("  Hello,   WORLD!! "), "hello world")
        self.assertIn("room", preprocess("The rooms are nice"))
        self.assertNotIn("the", preprocess("The rooms are nice"))

    def test_entity_extraction(self):
        ent = extract_entities("A deluxe room in Beachfront under $150 for 2 guests from 2026-12-01 to 2026-12-04",
                               ["Beachfront", "City Centre"], ["Deluxe", "Suite"], date(2026, 11, 17))
        self.assertEqual(ent["room_type"], "Deluxe")
        self.assertEqual(ent["location"], "Beachfront")
        self.assertEqual(ent["budget"], 150.0)
        self.assertEqual(ent["guests"], 2)
        self.assertEqual(ent["check_in"], date(2026, 12, 1))
        self.assertEqual(ent["check_out"], date(2026, 12, 4))

    def test_relative_dates_and_nights(self):
        ent = extract_entities("room tomorrow for 3 nights", [], [], date(2026, 11, 17))
        self.assertEqual(ent["check_in"], date(2026, 11, 18))
        self.assertEqual(ent["check_out"], date(2026, 11, 21))


class ChatbotTests(HotelTestCase):
    def test_price_answer_uses_database_prices(self):
        reply = self.ctx.chatbot.respond("How much is a deluxe room?")
        self.assertEqual(reply.intent, "PRICE")
        self.assertIn("$110.00", reply.text)
        self.assertIn("$140.00", reply.text)

    def test_availability_answer_detects_booked_room(self):
        self.make_booking(self.r_std, 0, 2)
        reply = self.ctx.chatbot.respond(f"Is room S1 available {self.d(0)} for 2 nights?".replace("room S1", "room 101"))
        self.assertEqual(reply.intent, "AVAILABILITY")

    def test_context_follow_up(self):
        ctx = {}
        self.ctx.chatbot.respond("How much is a suite?", ctx)
        self.assertEqual(ctx.get("room_type"), "Suite")

    def test_unknown_question_gets_helpful_reply(self):
        reply = self.ctx.chatbot.respond("what is the meaning of life")
        self.assertEqual(reply.intent, "UNKNOWN")
        self.assertIn("prices", reply.text)

    def test_facilities_lookup(self):
        reply = self.ctx.chatbot.respond("Which rooms have a sea view?")
        self.assertEqual(reply.intent, "FACILITIES")
        self.assertIn("Room D2", reply.text)


if __name__ == "__main__":
    unittest.main()