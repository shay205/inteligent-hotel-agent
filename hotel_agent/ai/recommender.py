"""Room recommendation: weighted scoring, ranking and explanations.

For every room we award points in five categories (total 100):
    location 30 | budget 25 | accommodation type 20 | capacity 15 | amenities 10
The points are added up, rooms are ranked, and each point source is turned
into a plain-English reason. No black box: every score can be explained.
"""
from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Tuple

from hotel_agent.config import MIN_RECOMMENDATION_SCORE, SCORING_WEIGHTS, TYPE_RANK, format_money
from hotel_agent.models.entities import Preferences, Room
from hotel_agent.services.booking_manager import BookingManager
from hotel_agent.services.room_manager import RoomManager


@dataclass
class Recommendation:
    room: Room
    score: float
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    breakdown: Dict[str, float] = field(default_factory=dict)
    available: bool = True


class RoomRecommender:
    def __init__(self, rooms: RoomManager, bookings: BookingManager, weights: Dict[str, float] = None):
        self.rooms = rooms
        self.bookings = bookings
        self.weights = weights or SCORING_WEIGHTS

    # ---------- scoring (pure function: no database access) ----------
    def score_room(self, room: Room, prefs: Preferences) -> Recommendation:
        w = self.weights
        reasons: List[str] = []
        warnings: List[str] = []
        breakdown: Dict[str, float] = {}

        # 1. Location
        if not prefs.location:
            breakdown["location"] = w["location"]
        elif room.location.lower() == prefs.location.lower():
            breakdown["location"] = w["location"]
            reasons.append(f"Located in your preferred area: {room.location}.")
        else:
            breakdown["location"] = 0
            warnings.append(f"In {room.location}, not your preferred area ({prefs.location}).")

        # 2. Budget (cheaper than budget earns slightly more; a little over earns partial credit)
        if not prefs.budget:
            breakdown["budget"] = w["budget"]
        elif room.price_per_night <= prefs.budget:
            ratio = room.price_per_night / prefs.budget
            breakdown["budget"] = w["budget"] * (0.85 + 0.15 * (1 - ratio))
            if ratio <= 0.7:
                reasons.append(f"{format_money(room.price_per_night)}/night is well under your budget of {format_money(prefs.budget)}.")
            else:
                reasons.append(f"{format_money(room.price_per_night)}/night fits your budget of {format_money(prefs.budget)}.")
        else:
            over = (room.price_per_night - prefs.budget) / prefs.budget
            breakdown["budget"] = w["budget"] * 0.5 * (1 - over / 0.2) if over <= 0.2 else 0
            warnings.append(f"{format_money(room.price_per_night - prefs.budget)} per night over your budget.")

        # 3. Accommodation type (neighbouring types get partial credit)
        if not prefs.accommodation_type:
            breakdown["type"] = w["type"]
        elif room.accommodation_type.lower() == prefs.accommodation_type.lower():
            breakdown["type"] = w["type"]
            reasons.append(f"Exactly the {room.accommodation_type} type you asked for.")
        else:
            gap = abs(TYPE_RANK.get(room.accommodation_type, 0) - TYPE_RANK.get(prefs.accommodation_type, 0))
            breakdown["type"] = w["type"] * {0: 0.5, 1: 0.5, 2: 0.25}.get(gap, 0)
            warnings.append(f"A {room.accommodation_type} room, not {prefs.accommodation_type}.")

        # 4. Capacity
        if prefs.guests > room.capacity:
            breakdown["capacity"] = 0
            warnings.append(f"Sleeps {room.capacity}, but you need space for {prefs.guests}.")
        elif room.capacity - prefs.guests <= 1:
            breakdown["capacity"] = w["capacity"]
            reasons.append(f"Comfortably sleeps {prefs.guests} guest(s) (capacity {room.capacity}).")
        else:
            breakdown["capacity"] = w["capacity"] * 0.8
            reasons.append(f"Plenty of space: sleeps up to {room.capacity}.")

        # 5. Amenities
        wanted = [a for a in prefs.amenities if a]
        if not wanted:
            breakdown["amenities"] = w["amenities"]
        else:
            have = {a.lower() for a in room.amenities}
            matched = [a for a in wanted if a.lower() in have]
            missing = [a for a in wanted if a.lower() not in have]
            breakdown["amenities"] = w["amenities"] * len(matched) / len(wanted)
            if matched:
                reasons.append("Includes requested amenities: " + ", ".join(matched) + ".")
            if missing:
                warnings.append("Missing: " + ", ".join(missing) + ".")

        score = round(sum(breakdown.values()), 1)
        breakdown = {k: round(val, 1) for k, val in breakdown.items()}
        if not reasons:
            reasons.append("Partial match with your preferences.")
        return Recommendation(room=room, score=score, reasons=reasons, warnings=warnings, breakdown=breakdown)

    # ---------- ranking ----------
    def recommend(self, prefs: Preferences, top_n: Optional[int] = None,
                  include_unavailable: bool = False,
                  min_score: float = MIN_RECOMMENDATION_SCORE) -> List[Recommendation]:
        """Rank suitable rooms from best to least suitable.

        Rooms that are too small, inactive or (when dates are given) already
        booked are detected here. Unavailable rooms are only returned when
        include_unavailable=True, flagged with available=False.
        """
        unavailable_ids = set()
        if prefs.has_dates:
            unavailable_ids = self.bookings.get_booked_room_ids(prefs.check_in, prefs.check_out)
        results: List[Recommendation] = []
        for room in self.rooms.list_rooms(active_only=True):
            if room.capacity < prefs.guests:
                continue
            rec = self.score_room(room, prefs)
            if rec.score < min_score:
                continue
            if room.id in unavailable_ids:
                if not include_unavailable:
                    continue
                rec.available = False
                rec.warnings.insert(0, "Already booked for the selected dates.")
            results.append(rec)
        results.sort(key=lambda r: (not r.available, -r.score, r.room.price_per_night))
        return results[:top_n] if top_n else results

    def recommend_with_fallback(self, prefs: Preferences, top_n: Optional[int] = None
                                ) -> Tuple[List[Recommendation], str]:
        """If nothing matches, relax preferences one at a time and say what was relaxed."""
        recs = self.recommend(prefs, top_n)
        if recs:
            return recs, ""
        relaxed = prefs
        dropped: List[str] = []
        steps = [("location", "location"), ("accommodation_type", "accommodation type"), ("budget", "budget")]
        for attr, label in steps:
            if getattr(relaxed, attr):
                relaxed = replace(relaxed, **{attr: None})
                dropped.append(label)
                recs = self.recommend(relaxed, top_n, min_score=0)
                if recs:
                    return recs, ("No room matched all your preferences, so these alternatives ignore your "
                                  + " and ".join(dropped) + ".")
        return [], "No rooms are available for these dates and number of guests. Try different dates."

    def find_alternatives(self, room_id: int, prefs: Preferences, top_n: int = 3) -> List[Recommendation]:
        """Suggest available rooms similar to one that is unavailable."""
        original = self.rooms.get_room(room_id)
        if original is None:
            return []
        similar = replace(
            prefs,
            location=prefs.location or original.location,
            accommodation_type=prefs.accommodation_type or original.accommodation_type,
            budget=prefs.budget or round(original.price_per_night * 1.2, 2),
        )
        recs = [r for r in self.recommend(similar, min_score=0) if r.room.id != room_id and r.available]
        for rec in recs:
            rec.reasons.insert(0, f"Similar to Room {original.room_number}, which is unavailable.")
        return recs[:top_n]