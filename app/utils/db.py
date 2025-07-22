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
        self._load_data()

    def _load_data(self):
        """Load recommendations from CSV file."""
        try:
            self._df = pd.read_csv(self.csv_path)
            # Clean up any NaN values in critical columns
            self._df = self._df.dropna(subset=["Recommendation", "Evidence"])
            print(f"Loaded {len(self._df)} recommendations from {self.csv_path}")
        except Exception as e:
            print(f"Error loading recommendations: {e}")
            self._df = pd.DataFrame()

    def get_all_recommendations(self) -> pd.DataFrame:
        """Get all recommendations as DataFrame."""
        return self._df.copy()

    def get_random_recommendation(self, topic: str = None) -> Optional[Dict]:
        """Get a random recommendation, optionally filtered by topic."""
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
            "theme": rec["Theme"],
            "topic": rec["Topic"],
            "recommendation": rec["Recommendation"],
            "grade": rec["Grade"],
            "evidence": rec["Evidence"],
            "references": rec["References"],
            "link": rec.get("Link", ""),
        }

    def list_topics(self) -> List[str]:
        """Get list of all available topics."""
        if self._df.empty:
            return []
        return sorted(self._df["Topic"].dropna().unique().tolist())

    def list_themes(self) -> List[str]:
        """Get list of all available themes."""
        if self._df.empty:
            return []
        return sorted(self._df["Theme"].dropna().unique().tolist())

    def get_topic_count(self, topic: str) -> int:
        """Get number of recommendations for a specific topic."""
        if self._df.empty:
            return 0
        return len(self._df[self._df["Topic"] == topic])

    def get_recommendations_by_topic(self, topic: str) -> List[Dict]:
        """Get all recommendations for a specific topic."""
        if self._df.empty:
            return []

        topic_df = self._df[self._df["Topic"] == topic]
        recommendations = []

        for _, rec in topic_df.iterrows():
            recommendations.append(
                {
                    "theme": rec["Theme"],
                    "topic": rec["Topic"],
                    "recommendation": rec["Recommendation"],
                    "grade": rec["Grade"],
                    "evidence": rec["Evidence"],
                    "references": rec["References"],
                    "link": rec.get("Link", ""),
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
