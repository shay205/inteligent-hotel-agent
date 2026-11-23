"""Text cleaning for customer messages.

Pipeline:  raw text -> lowercase -> tokenize -> (remove stop-words) -> light stemming
"""
import re
from typing import List

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "to", "of", "and", "or", "in", "on",
    "at", "for", "with", "me", "my", "i", "you", "your", "we", "our", "it", "this", "that",
    "do", "does", "did", "can", "could", "would", "will", "please", "there", "any", "some",
    "have", "has", "am", "so", "just", "about", "tell", "want", "like", "need",
}

# words, "$150", "2026-06-01", "wi-fi", "3.5" are each one token
TOKEN_PATTERN = re.compile(r"\$?[a-z0-9]+(?:[-.][a-z0-9]+)*")


def tokenize(text) -> List[str]:
    if not isinstance(text, str):
        return []
    return TOKEN_PATTERN.findall(text.lower())


def clean_text(text) -> str:
    """Lowercase, remove punctuation/extra spaces."""
    return " ".join(tokenize(text))


def remove_stopwords(tokens: List[str]) -> List[str]:
    return [t for t in tokens if t not in STOPWORDS]


def stem(word: str) -> str:
    """A tiny stemmer: rooms -> room, facilities -> facility, booking -> book."""
    if len(word) > 4 and word.endswith("ies"):
        word = word[:-3] + "y"
    elif len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        word = word[:-1]
    if len(word) > 5 and word.endswith("ing"):
        word = word[:-3]
    return word


def preprocess(text) -> List[str]:
    """Full pipeline: clean -> tokens -> remove stop-words -> stem."""
    return [stem(t) for t in remove_stopwords(tokenize(text))]


def stemmed_text(text) -> str:
    """Stemmed tokens (stop-words kept, so phrases like 'how much' still match)."""
    return " ".join(stem(t) for t in tokenize(text))