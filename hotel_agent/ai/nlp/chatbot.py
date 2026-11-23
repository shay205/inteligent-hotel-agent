"""Conversational assistant: message -> intent -> data lookup -> reply.

The bot never invents hotel facts. Every price, room and availability answer
comes from the SQLite database through the manager classes.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional

from hotel_agent.ai.nlp.entity_extractor import extract_entities
from hotel_agent.ai.nlp.intent_classifier import IntentClassifier
from hotel_agent.ai.nlp.preprocessing import clean_text
from hotel_agent.ai.recommender import Recommendation, RoomRecommender
from hotel_agent.ai.service_recommender import ServiceRecommender, extract_interests
from hotel_agent.config import (CHECK_IN_TIME, CHECK_OUT_TIME, HOTEL_FACILITIES,
                                HOTEL_NAME, format_money)
from hotel_agent.models.entities import Preferences, Room, make_reference
from hotel_agent.services.booking_manager import BookingManager
from hotel_agent.services.room_manager import RoomManager
from hotel_agent.services.service_manager import ServiceManager

# details remembered between messages so follow-up questions work
STICKY_KEYS = ["room_type", "location", "budget", "guests", "check_in", "check_out"]

SERVICE_KEYWORDS = {
    "Spa": ["spa", "massage", "sauna", "wellness"],
    "Airport Transfer": ["airport", "transfer", "shuttle", "pickup", "taxi"],
    "Restaurant": ["restaurant", "dinner", "dining", "table"],
    "Room Service": ["room service", "in-room", "snack"],
    "Laundry": ["laundry", "washing"],
    "Business": ["business", "meeting", "printing"],
    "Tour": ["tour", "sightseeing", "excursion"],
    "Childcare": ["kids", "childcare", "babysitting", "children"],
}


@dataclass
class ChatResponse:
    text: str
    intent: str
    confidence: float
    entities: Dict = field(default_factory=dict)


class HotelChatbot:
    def __init__(self, rooms: RoomManager, bookings: BookingManager, services: ServiceManager,
                 recommender: RoomRecommender, service_recommender: ServiceRecommender,
                 classifier: IntentClassifier = None):
        self.rooms = rooms
        self.bookings = bookings
        self.services = services
        self.recommender = recommender
        self.service_recommender = service_recommender
        self.classifier = classifier or IntentClassifier()

    # ---------- main entry point ----------
    def respond(self, message: str, context: Optional[Dict] = None, today: date = None) -> ChatResponse:
        context = context if context is not None else {}
        today = today or date.today()
        if not isinstance(message, str) or not clean_text(message):
            return ChatResponse("Please type a question, for example: *How much is a deluxe room?*", "UNKNOWN", 0.0)
        if len(message) > 500:
            return ChatResponse("That message is a bit long. Could you shorten it to a sentence or two?", "UNKNOWN", 0.0)

        result = self.classifier.classify(message)
        entities = extract_entities(message, self.rooms.get_locations(), self.rooms.get_types(), today)
        entities["interests"] = extract_interests(message)

        merged = {k: context[k] for k in STICKY_KEYS if context.get(k) is not None}
        for key in STICKY_KEYS:
            if key in entities:
                merged[key] = entities[key]
        if "check_in" in entities and "check_out" not in entities:
            merged.pop("check_out", None)
        for key in ("amenities", "interests", "room_number", "booking_id", "nights"):
            if entities.get(key):
                merged[key] = entities[key]

        handler = getattr(self, "_on_" + result.intent.lower(), self._on_unknown)
        text = handler(message, merged, today)

        for key in STICKY_KEYS:
            if merged.get(key) is not None:
                context[key] = merged[key]
        return ChatResponse(text, result.intent, result.confidence, entities)

    # ---------- helpers ----------
    def _prefs(self, ent: Dict) -> Preferences:
        check_in, check_out = ent.get("check_in"), ent.get("check_out")
        if check_in and not check_out:
            check_out = check_in + timedelta(days=ent.get("nights") or 1)
        return Preferences(
            location=ent.get("location"), budget=ent.get("budget"),
            accommodation_type=ent.get("room_type"), check_in=check_in, check_out=check_out,
            guests=ent.get("guests") or 1, amenities=list(ent.get("amenities") or []),
            interests=list(ent.get("interests") or []))

    @staticmethod
    def _room_line(room: Room) -> str:
        return (f"- **Room {room.room_number}** - {room.name} ({room.accommodation_type}, {room.location}): "
                f"{format_money(room.price_per_night)}/night, sleeps {room.capacity}")

    @staticmethod
    def _rec_line(rec: Recommendation) -> str:
        r = rec.room
        return (f"- **Room {r.room_number}** - {r.name} ({r.accommodation_type}, {r.location}): "
                f"{format_money(r.price_per_night)}/night - match score **{rec.score:.0f}/100**\n"
                f"  *Why:* {' '.join(rec.reasons[:2])}")

    # ---------- intent handlers ----------
    def _on_greeting(self, message, ent, today) -> str:
        return (f"Hello! I'm the virtual assistant for **{HOTEL_NAME}**. I can help with room prices, availability, "
                "facilities, bookings and hotel services. What would you like to know?")

    def _on_help(self, message, ent, today) -> str:
        return ("I can help you with:\n- **Prices** - *How much is a deluxe room?*\n"
                "- **Availability** - *Is a family room free on 2026-12-20 for 3 nights?*\n"
                "- **Facilities** - *Which rooms have a sea view?*\n"
                "- **Recommendations** - *Suggest a room under $150 for 2 guests in the city centre*\n"
                "- **Bookings and cancellations** - *How do I book a room?*\n"
                "- **Services** - *Do you offer airport transfers or a spa?*")

    def _on_thanks(self, message, ent, today) -> str:
        return "You're welcome! Let me know if there is anything else I can help with."

    def _on_goodbye(self, message, ent, today) -> str:
        return "Goodbye! Thank you for chatting with us."

    def _on_checkin_info(self, message, ent, today) -> str:
        return (f"Check-in starts at **{CHECK_IN_TIME}** and check-out is by **{CHECK_OUT_TIME}**. "
                "The check-out day is free for the next guest, so back-to-back stays never overlap.")

    def _on_price(self, message, ent, today) -> str:
        rooms = self.rooms.list_rooms(active_only=True)
        if not rooms:
            return "There are no rooms in the system yet."
        if ent.get("room_number"):
            room = self.rooms.get_by_number(ent["room_number"])
            if room is None:
                return f"I couldn't find a room numbered {ent['room_number']}."
            return f"Room {room.room_number} ({room.name}) costs **{format_money(room.price_per_night)} per night**."
        lowered = message.lower()
        if any(w in lowered for w in ("cheapest", "cheap", "cheaper", "affordable", "lowest")):
            pool = [r for r in rooms if r.accommodation_type == ent.get("room_type")] if ent.get("room_type") else rooms
            if ent.get("budget"):
                pool = [r for r in pool if r.price_per_night <= ent["budget"]] or pool
            cheapest = sorted(pool, key=lambda r: r.price_per_night)[:3]
            return "Our most affordable options right now:\n" + "\n".join(self._room_line(r) for r in cheapest)
        if ent.get("budget") and not ent.get("room_type"):
            within = sorted([r for r in rooms if r.price_per_night <= ent["budget"]], key=lambda r: r.price_per_night)
            if not within:
                lowest = min(rooms, key=lambda r: r.price_per_night)
                return (f"No room is priced at or below {format_money(ent['budget'])}. "
                        f"Our lowest rate is {format_money(lowest.price_per_night)} per night.")
            return (f"{len(within)} room(s) cost {format_money(ent['budget'])} or less per night:\n"
                    + "\n".join(self._room_line(r) for r in within[:6]))
        if ent.get("room_type"):
            subset = [r for r in rooms if r.accommodation_type == ent["room_type"]]
            if subset:
                prices = [r.price_per_night for r in subset]
                text = (f"**{ent['room_type']}** rooms cost **{format_money(min(prices))} to {format_money(max(prices))}** "
                        f"per night ({len(subset)} rooms):\n" + "\n".join(self._room_line(r) for r in subset[:6]))
                if ent.get("check_in") and ent.get("check_out"):
                    nights = (ent["check_out"] - ent["check_in"]).days
                    text += f"\n\nFor {nights} night(s) that is {format_money(min(prices) * nights)} to {format_money(max(prices) * nights)}."
                return text
        lines = []
        for t in sorted({r.accommodation_type for r in rooms}):
            prices = [r.price_per_night for r in rooms if r.accommodation_type == t]
            lines.append(f"- **{t}**: {format_money(min(prices))} - {format_money(max(prices))} per night ({len(prices)} rooms)")
        return "Here are our room rates per night:\n" + "\n".join(lines) + "\n\nAsk about a specific type, e.g. *How much is a suite?*"

    def _on_availability(self, message, ent, today) -> str:
        prefs = self._prefs(ent)
        assumed = ""
        if prefs.check_in and prefs.check_in < today:
            return "That date is in the past. Please give me a check-in date from today onwards."
        if not prefs.has_dates:
            prefs.check_in = today
            prefs.check_out = today + timedelta(days=1)
            assumed = "No dates given, so I checked **tonight**. "
        elif "check_out" not in ent and not ent.get("nights") and "check_out" not in ent:
            assumed = "I assumed a 1-night stay. "
        if prefs.has_dates and (prefs.check_out - prefs.check_in).days < 1:
            return "The check-out date must be after the check-in date."
        period = f"{prefs.check_in.isoformat()} to {prefs.check_out.isoformat()}"
        guests_note = f" for {prefs.guests} guests" if prefs.guests > 1 else ""

        if ent.get("room_number"):
            room = self.rooms.get_by_number(ent["room_number"])
            if room is None:
                return f"I couldn't find a room numbered {ent['room_number']}."
            if self.bookings.is_available(room.id, prefs.check_in, prefs.check_out):
                return f"{assumed}Room {room.room_number} ({room.name}) is **available** for {period} at {format_money(room.price_per_night)}/night."
            alts = self.recommender.find_alternatives(room.id, prefs, 3)
            text = f"{assumed}Room {room.room_number} is **not available** for {period}."
            if alts:
                text += " Similar rooms that are free:\n" + "\n".join(self._rec_line(a) for a in alts)
            return text

        free = self.bookings.get_available_rooms(prefs.check_in, prefs.check_out, prefs.guests)
        if prefs.accommodation_type:
            free = [r for r in free if r.accommodation_type == prefs.accommodation_type]
        if prefs.location:
            free = [r for r in free if r.location == prefs.location]
        label = " ".join(x for x in [prefs.accommodation_type, "room(s)"] if x)
        if free:
            free.sort(key=lambda r: r.price_per_night)
            return (f"{assumed}**{len(free)} {label}** available for {period}{guests_note}:\n"
                    + "\n".join(self._room_line(r) for r in free[:6])
                    + ("\n\n...and more in the *Find a Room* page." if len(free) > 6 else ""))
        recs, note = self.recommender.recommend_with_fallback(prefs, 3)
        text = f"{assumed}Sorry, no {label} are available for {period}{guests_note}."
        if recs:
            text += f" {note}\n" + "\n".join(self._rec_line(r) for r in recs)
        else:
            text += " Please try different dates."
        return text

    def _on_facilities(self, message, ent, today) -> str:
        wanted = ent.get("amenities") or []
        rooms = self.rooms.list_rooms(active_only=True)
        if wanted:
            matches = [r for r in rooms if all(w.lower() in [a.lower() for a in r.amenities] for w in wanted)]
            if ent.get("room_type"):
                matches = [r for r in matches if r.accommodation_type == ent["room_type"]]
            if not matches:
                return f"No active room currently offers all of: {', '.join(wanted)}."
            matches.sort(key=lambda r: r.price_per_night)
            return (f"{len(matches)} room(s) include **{', '.join(wanted)}**:\n"
                    + "\n".join(self._room_line(r) for r in matches[:6]))
        if ent.get("room_type"):
            subset = [r for r in rooms if r.accommodation_type == ent["room_type"]]
            if subset:
                common = set(subset[0].amenities)
                union = set()
                for r in subset:
                    common &= set(r.amenities)
                    union |= set(r.amenities)
                text = f"All **{ent['room_type']}** rooms include: {', '.join(sorted(common)) or 'basic amenities'}."
                extras = sorted(union - common)
                if extras:
                    text += f"\nSome also offer: {', '.join(extras)}."
                return text
        return ("Hotel facilities:\n" + "\n".join(f"- {f}" for f in HOTEL_FACILITIES)
                + "\n\nAsk about a room amenity, e.g. *Which rooms have a balcony?*")

    def _on_booking(self, message, ent, today) -> str:
        if ent.get("booking_id"):
            details = self.bookings.get_booking_details(ent["booking_id"])
            if details is None:
                return f"I couldn't find a booking with reference {make_reference(ent['booking_id'])}."
            return (f"Booking **{details['reference']}**: Room {details['room_number']} ({details['room_name']}), "
                    f"{details['check_in']} to {details['check_out']}, {details['guests']} guest(s), "
                    f"total {format_money(details['total_price'])}. Status: **{details['status']}**.")
        steps = ("To book a room:\n1. Open **Find a Room** to see ranked recommendations, or go straight to **Booking Management**.\n"
                 "2. Choose dates and guests, then pick one of the available rooms.\n"
                 "3. Enter the guest's name, email and phone, then press *Confirm reservation*.\n"
                 "4. Download the booking confirmation.\n\n*Bookings are simulated for this demonstration.*")
        if ent.get("check_in") or ent.get("room_type") or ent.get("budget"):
            recs, _ = self.recommender.recommend_with_fallback(self._prefs(ent), 3)
            if recs:
                steps += "\n\nBased on what you told me, I suggest:\n" + "\n".join(self._rec_line(r) for r in recs)
        return steps

    def _on_cancellation(self, message, ent, today) -> str:
        text = ("Bookings can be cancelled in **Booking Management -> Cancel Booking**. "
                "Once cancelled, the room becomes available again for those dates (free cancellation).")
        if ent.get("booking_id"):
            details = self.bookings.get_booking_details(ent["booking_id"])
            if details:
                text += f"\n\nBooking {details['reference']} is currently **{details['status']}**."
            else:
                text += f"\n\nI couldn't find booking {make_reference(ent['booking_id'])}."
        return text

    def _on_services(self, message, ent, today) -> str:
        services = self.services.list_services(active_only=True)
        if not services:
            return "No additional services are set up yet."
        lowered = message.lower()
        categories = [c for c, words in SERVICE_KEYWORDS.items() if any(w in lowered for w in words)]
        chosen = [s for s in services if s.category in categories] if categories else services
        lines: List[str] = []
        for category in sorted({s.category for s in chosen}):
            lines.append(f"**{category}**")
            lines += [f"- {s.name} - {format_money(s.price)}: {s.description}" for s in chosen if s.category == category]
        text = "Our additional services:\n" + "\n".join(lines)
        if categories:
            text += "\n\nYou can order these in the **Additional Services** page after booking."
        return text

    def _on_recommendation(self, message, ent, today) -> str:
        keys = ("room_type", "location", "budget", "guests", "check_in", "amenities")
        if not any(ent.get(k) for k in keys):
            return ("Tell me a little about your stay and I'll rank the best rooms, for example:\n"
                    "*Suggest a deluxe room in the city centre under $150 for 2 guests from 2026-12-20 to 2026-12-23.*")
        prefs = self._prefs(ent)
        if prefs.check_in and prefs.check_in < today:
            return "That date is in the past. Please give me a check-in date from today onwards."
        recs, note = self.recommender.recommend_with_fallback(prefs, 3)
        if not recs:
            return note
        text = ("Here are my top picks for you:\n" + "\n".join(self._rec_line(r) for r in recs))
        if note:
            text = note + "\n" + text
        extras = self.service_recommender.recommend(prefs, 2)
        if extras:
            text += "\n\nYou might also enjoy: " + "; ".join(f"{s.service.name} ({format_money(s.service.price)})" for s in extras) + "."
        return text

    def _on_unknown(self, message, ent, today) -> str:
        return ("I'm not sure I understood that. I can answer questions about **prices**, **availability**, "
                "**facilities**, **bookings** and **hotel services**. Try: *How much is a suite?* or "
                "*Is there a room available tomorrow?*")