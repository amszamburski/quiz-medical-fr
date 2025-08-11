import pandas as pd
import os
import random
from typing import List, Dict, Optional


class RecommendationsDB:
    """Handles loading and querying medical recommendations data."""

    def __init__(self, csv_path: str = None):
        if csv_path is None:
            csv_path = os.path.join(
                os.path.dirname(__file__), "../../data/recommendations.csv"
            )
        self.csv_path = csv_path
        self._df = None
        self._mtime = None
        self._load_data()

    def _load_data(self):
        """Load recommendations from CSV file."""
        try:
            self._df = pd.read_csv(self.csv_path)
            # Clean up any NaN values in critical columns
            self._df = self._df.dropna(subset=["Recommendation", "Evidence"])
            try:
                self._mtime = os.path.getmtime(self.csv_path)
            except Exception:
                self._mtime = None
            print(f"Loaded {len(self._df)} recommendations from {self.csv_path}")
        except Exception as e:
            print(f"Error loading recommendations: {e}")
            self._df = pd.DataFrame()
            self._mtime = None

    def _maybe_reload(self):
        """Reload CSV if the file changed on disk since last load."""
        try:
            mtime = os.path.getmtime(self.csv_path)
        except Exception:
            mtime = None
        if self._mtime is None or (mtime is not None and mtime != self._mtime):
            self._load_data()

    def get_all_recommendations(self) -> pd.DataFrame:
        """Get all recommendations as DataFrame."""
        self._maybe_reload()
        return self._df.copy()

    def get_random_recommendation(self, topic: str = None) -> Optional[Dict]:
        """Get a random recommendation, optionally filtered by topic."""
        def _safe(v):
            try:
                import pandas as pd  # local import to avoid circular in some envs
                return "" if pd.isna(v) else str(v)
            except Exception:
                return "" if v is None else str(v)

        self._maybe_reload()
        if self._df.empty:
            return None

        df = self._df
        if topic:
            df = df[df["Topic"] == topic]
            if df.empty:
                return None

        # Select random recommendation
        rec = df.sample(n=1).iloc[0]
        return {
            "theme": _safe(rec.get("Theme")),
            "topic": _safe(rec.get("Topic")),
            "recommendation": _safe(rec.get("Recommendation")),
            "grade": _safe(rec.get("Grade")),
            "evidence": _safe(rec.get("Evidence")),
            "references": _safe(rec.get("References")),
            "link": _safe(rec.get("Link")),
        }

    def list_topics(self) -> List[str]:
        """Get list of all available topics."""
        self._maybe_reload()
        if self._df.empty:
            return []
        return sorted(self._df["Topic"].dropna().unique().tolist())

    def list_themes(self) -> List[str]:
        """Get list of all available themes."""
        self._maybe_reload()
        if self._df.empty:
            return []
        return sorted(self._df["Theme"].dropna().unique().tolist())

    def get_topic_count(self, topic: str) -> int:
        """Get number of recommendations for a specific topic."""
        self._maybe_reload()
        if self._df.empty:
            return 0
        return len(self._df[self._df["Topic"] == topic])

    def get_recommendations_by_topic(self, topic: str) -> List[Dict]:
        """Get all recommendations for a specific topic."""
        self._maybe_reload()
        if self._df.empty:
            return []

        topic_df = self._df[self._df["Topic"] == topic]
        recommendations = []

        def _safe(v):
            try:
                import pandas as pd
                return "" if pd.isna(v) else str(v)
            except Exception:
                return "" if v is None else str(v)

        for _, rec in topic_df.iterrows():
            recommendations.append(
                {
                    "theme": _safe(rec.get("Theme")),
                    "topic": _safe(rec.get("Topic")),
                    "recommendation": _safe(rec.get("Recommendation")),
                    "grade": _safe(rec.get("Grade")),
                    "evidence": _safe(rec.get("Evidence")),
                    "references": _safe(rec.get("References")),
                    "link": _safe(rec.get("Link")),
                }
            )

        return recommendations


# Global instance
recommendations_db = RecommendationsDB()


def load_recommendations() -> RecommendationsDB:
    """Load recommendations database."""
    return recommendations_db


def list_topics() -> List[str]:
    """Get list of available topics."""
    return recommendations_db.list_topics()


def get_random_recommendation(topic: str = None) -> Optional[Dict]:
    """Get a random recommendation."""
    return recommendations_db.get_random_recommendation(topic)
