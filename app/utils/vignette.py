"""
Vignette generation and question management.
"""

from typing import Optional, Dict
from .db import get_random_recommendation
from .openai_client import get_openai_client


def generate_vignette_and_question(topic: str = None, recommendation: Dict = None) -> Optional[Dict]:
    """
    Generate a clinical vignette and question from a random recommendation.

    Args:
        topic: Optional topic to filter recommendations
        recommendation: Optional explicit recommendation dict to use

    Returns:
        Dict with vignette, question, and recommendation data
    """
    # Choose recommendation
    if recommendation is None:
        recommendation = get_random_recommendation(topic)
        if not recommendation:
            return None

    # Generate vignette and question using OpenAI
    client = get_openai_client()
    result = client.generate_vignette_and_question(recommendation)
    if not result:
        return None

    # Combine with recommendation data
    return {
        "vignette": result["vignette"],
        "question": result["question"],
        "recommendation": recommendation,
        "topic": recommendation["topic"],
        "theme": recommendation["theme"],
    }
