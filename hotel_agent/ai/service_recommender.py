"""Suggest additional services from the customer's preferences and interests."""
from dataclasses import dataclass
from typing import Dict, List

from hotel_agent.ai.nlp.preprocessing import stem, tokenize
from hotel_agent.models.entities import Preferences, Service
from hotel_agent.services.service_manager import ServiceManager

INTEREST_KEYWORDS: Dict[str, List[str]] = {
    "relaxation": ["spa", "massage", "relax", "relaxing", "relaxation", "wellness", "sauna"],
    "romantic": ["romantic", "honeymoon", "anniversary", "couple"],
    "business": ["business", "meeting", "work", "conference", "laptop"],
    "family": ["family", "kids", "children", "child", "toddler"],
    "dining": ["dinner", "restaurant", "food", "dining", "lunch", "meal"],
    "travel": ["airport", "flight", "transfer", "pickup", "shuttle", "taxi"],
    "sightseeing": ["tour", "sightseeing", "explore", "excursion", "attractions"],
    "laundry": ["laundry", "washing", "clothes"],
}

# interest -> {service category: points}
INTEREST_RULES: Dict[str, Dict[str, int]] = {
    "relaxation": {"Spa": 3},
    "romantic": {"Restaurant": 3, "Spa": 2},
    "business": {"Business": 3, "Room Service": 1, "Laundry": 1},
    "family": {"Childcare": 3, "Tour": 1},
    "dining": {"Restaurant": 3, "Room Service": 2},
    "travel": {"Airport Transfer": 3},
    "sightseeing": {"Tour": 3},
    "laundry": {"Laundry": 3},
}

INTEREST_LABELS = {
    "relaxation": "Relaxation / spa", "romantic": "Romantic stay", "business": "Business travel",
    "family": "Travelling with children", "dining": "Dining", "travel": "Airport / transport",
    "sightseeing": "Sightseeing",
}


def extract_interests(text: str) -> List[str]:
    tokens = {stem(t) for t in tokenize(text)}
    return [name for name, words in INTEREST_KEYWORDS.items() if tokens & {stem(w) for w in words}]


@dataclass
class ServiceSuggestion:
    service: Service
    score: float
    reason: str


class ServiceRecommender:
    def __init__(self, services: ServiceManager):
        self.services = services

    def recommend(self, prefs: Preferences, top_n: int = 5) -> List[ServiceSuggestion]:
        points: Dict[str, float] = {}
        why: Dict[str, List[str]] = {}

        def add(category: str, pts: float, reason: str) -> None:
            points[category] = points.get(category, 0) + pts
            if reason not in why.setdefault(category, []):
                why[category].append(reason)

        for interest in prefs.interests:
            for category, pts in INTEREST_RULES.get(interest, {}).items():
                add(category, pts, f"matches your interest: {INTEREST_LABELS.get(interest, interest).lower()}")

        location = (prefs.location or "").lower()
        accommodation = prefs.accommodation_type or ""
        if "airport" in location:
            add("Airport Transfer", 3, "you are staying on the airport side")
        if "beach" in location:
            add("Tour", 1, "popular with beachfront guests")
            add("Spa", 1, "a perfect pairing with a beach stay")
        if prefs.nights >= 4:
            add("Laundry", 2, f"useful for a {prefs.nights}-night stay")
            add("Room Service", 1, "convenient on a longer stay")
        if prefs.guests >= 4 or accommodation == "Family":
            add("Childcare", 2, "ideal for a family group")
            add("Restaurant", 1, "a table for the whole group")
        if accommodation in ("Suite", "Executive"):
            add("Spa", 2, f"a treat that suits a {accommodation} stay")
            add("Airport Transfer", 1, "a smooth arrival for premium guests")
        if accommodation == "Executive":
            add("Business", 2, "supports business travellers")
        if prefs.budget and prefs.budget >= 250:
            add("Spa", 1, "fits a premium budget")

        suggestions: List[ServiceSuggestion] = []
        active = self.services.list_services(active_only=True)
        for service in active:
            pts = points.get(service.category, 0)
            if pts > 0:
                reason = "Suggested because " + "; ".join(why[service.category]) + "."
                suggestions.append(ServiceSuggestion(service, round(pts - service.price / 10000, 3), reason))
        if not suggestions:  # nothing specific -> popular defaults
            for service in active:
                if service.category in ("Airport Transfer", "Restaurant"):
                    suggestions.append(ServiceSuggestion(service, 0.1, "Popular with our guests."))
        suggestions.sort(key=lambda s: (-s.score, s.service.price))
        return suggestions[:top_n]