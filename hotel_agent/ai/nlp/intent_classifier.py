"""Keyword-based intent classification.

How it works (easy to explain in a demo):
1. Clean + stem the message.
2. For every intent, count keyword hits (+1 per word) and phrase hits (+2 per phrase).
3. The intent with the highest score wins. Ties are broken by a priority list.
4. If nothing matches, the intent is UNKNOWN.
"""
from dataclasses import dataclass, field
from typing import Dict, List

from hotel_agent.ai.nlp.preprocessing import stem, stemmed_text, tokenize

INTENT_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "GREETING": {
        "words": ["hello", "hi", "hey", "greetings", "howdy"],
        "phrases": ["good morning", "good afternoon", "good evening"],
    },
    "PRICE": {
        "words": ["price", "cost", "rate", "cheap", "cheaper", "cheapest", "expensive", "afford",
                  "affordable", "pay", "fee", "charge", "tariff", "budget", "dollar", "pricing"],
        "phrases": ["how much", "per night", "price range"],
    },
    "AVAILABILITY": {
        "words": ["available", "availability", "vacancy", "vacant", "free", "open", "unoccupied"],
        "phrases": ["any room", "rooms left", "still have", "is there"],
    },
    "FACILITIES": {
        "words": ["facility", "amenity", "wifi", "wi-fi", "internet", "pool", "swimming", "gym",
                  "fitness", "parking", "balcony", "kitchen", "kitchenette", "bathtub", "tv",
                  "television", "minibar", "aircon", "view", "equipped", "include", "breakfast"],
        "phrases": ["air conditioning", "come with", "comes with", "mini bar", "what is in"],
    },
    "BOOKING": {
        "words": ["book", "booked", "booking", "reserve", "reservation", "reserved", "confirm",
                  "confirmation"],
        "phrases": ["i want to book", "would like to book", "make a reservation", "my booking"],
    },
    "CANCELLATION": {
        "words": ["cancel", "cancelled", "cancellation", "refund", "canceling", "cancell"],
        "phrases": ["cancel my booking", "cancel booking", "cancel reservation"],
    },
    "SERVICES": {
        "words": ["service", "spa", "massage", "laundry", "transfer", "shuttle", "pickup", "taxi",
                  "restaurant", "dinner", "dining", "tour", "babysitting", "childcare", "concierge",
                  "sauna"],
        "phrases": ["room service", "airport transfer", "airport pickup", "book a table"],
    },
    "RECOMMENDATION": {
        "words": ["recommend", "recommendation", "suggest", "suggestion", "suitable", "ideal",
                  "best", "perfect", "advise"],
        "phrases": ["looking for", "find me", "help me choose", "help me find", "right room",
                    "good for", "which room should", "what room should"],
    },
    "CHECKIN_INFO": {
        "words": ["check-in", "check-out", "checkin", "checkout", "policy", "time", "hours"],
        "phrases": ["check in time", "check out time", "early check", "late check"],
    },
    "THANKS": {"words": ["thanks", "thank", "thx", "appreciate", "cheers"], "phrases": []},
    "GOODBYE": {"words": ["bye", "goodbye", "farewell"], "phrases": ["see you", "see ya"]},
    "HELP": {
        "words": ["help", "assist", "assistance"],
        "phrases": ["what can you do", "how do you work", "what can i ask"],
    },
}

# When two intents get the same score, the earlier one in this list wins.
INTENT_PRIORITY = [
    "CANCELLATION", "BOOKING", "RECOMMENDATION", "AVAILABILITY", "PRICE", "FACILITIES",
    "SERVICES", "CHECKIN_INFO", "GREETING", "THANKS", "GOODBYE", "HELP",
]


@dataclass
class IntentResult:
    intent: str
    confidence: float
    scores: Dict[str, int] = field(default_factory=dict)
    matched: List[str] = field(default_factory=list)


class IntentClassifier:
    def __init__(self, keywords: Dict[str, Dict[str, List[str]]] = None, priority: List[str] = None):
        keywords = keywords or INTENT_KEYWORDS
        self.priority = priority or INTENT_PRIORITY
        # Pre-compute stemmed versions so matching is consistent.
        self._words = {i: {stem(w) for w in spec.get("words", [])} for i, spec in keywords.items()}
        self._phrases = {
            i: [" ".join(stem(t) for t in tokenize(p)) for p in spec.get("phrases", [])]
            for i, spec in keywords.items()
        }

    def classify(self, message) -> IntentResult:
        tokens = {stem(t) for t in tokenize(message)}
        haystack = f" {stemmed_text(message)} "
        scores: Dict[str, int] = {}
        matched: Dict[str, List[str]] = {}
        for intent in self._words:
            hits = sorted(self._words[intent] & tokens)
            phrase_hits = [p for p in self._phrases[intent] if p and f" {p} " in haystack]
            score = len(hits) + 2 * len(phrase_hits)
            if score:
                scores[intent] = score
                matched[intent] = hits + phrase_hits
        if not scores:
            return IntentResult("UNKNOWN", 0.0, {}, [])
        best = max(scores.values())
        candidates = [i for i, s in scores.items() if s == best]
        order = {name: n for n, name in enumerate(self.priority)}
        winner = min(candidates, key=lambda i: order.get(i, 999))
        share = best / sum(scores.values())
        strength = min(1.0, best / 3.0)
        confidence = round(0.5 * share + 0.5 * strength, 2)
        return IntentResult(winner, confidence, scores, matched[winner])