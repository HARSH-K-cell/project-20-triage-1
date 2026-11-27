from difflib import SequenceMatcher
import re

class TicketDeduplicator:
    """Lightweight duplicate checker; does not require FAISS or ML downloads."""
    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold
        self.ticket_ids = []
        self.ticket_texts = []

    def _normalize(self, text: str) -> str:
        return " ".join(re.findall(r"[a-z0-9]+", (text or "").lower()))

    def check_and_add(self, ticket_id: int, text: str):
        normalized = self._normalize(text)
        best_score = 0.0
        best_index = -1

        for i, existing in enumerate(self.ticket_texts):
            score = SequenceMatcher(None, normalized, self._normalize(existing)).ratio()
            if score > best_score:
                best_score, best_index = score, i

        if best_index >= 0 and best_score >= self.threshold:
            return {
                "is_duplicate": True,
                "similarity": round(best_score * 100, 2),
                "matched_ticket_id": self.ticket_ids[best_index],
                "matched_text": self.ticket_texts[best_index],
            }

        self.ticket_ids.append(ticket_id)
        self.ticket_texts.append(text)
        return {
            "is_duplicate": False,
            "similarity": round(best_score * 100, 2),
            "matched_ticket_id": None,
            "matched_text": None,
        }

deduplicator = TicketDeduplicator(threshold=0.85)
