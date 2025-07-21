"""
Answer evaluation and scoring system.
"""

from typing import Dict, Optional
from .openai_client import get_openai_client


def evaluate_answer(user_answer: str, question_data: Dict) -> Optional[Dict]:
    """
    Evaluate user's answer and provide score and feedback.

    Args:
        user_answer: User's free-text answer
        question_data: Dict containing vignette, question, and recommendation

    Returns:
        Dict with score, feedback, and educational content
    """
    print(f"DEBUG: Starting evaluation for answer: {user_answer[:50]}...")

    if not user_answer or not question_data:
        print("DEBUG: No answer or question data provided")
        return {
            "score": 0,
            "feedback": "Aucune réponse fournie.",
            "educational_content": "Veuillez fournir une réponse pour recevoir un feedback.",
        }

    try:
        # Evaluate the answer
        print("DEBUG: Getting OpenAI client...")
        client = get_openai_client()
        print(f"DEBUG: Client type: {type(client)}")

        print("DEBUG: Calling evaluate_answer...")
        evaluation = client.evaluate_answer(
            user_answer=user_answer.strip(),
            correct_recommendation=question_data["recommendation"],
            vignette=question_data["vignette"],
            question=question_data["question"],
        )
        print(f"DEBUG: Evaluation received: {evaluation}")

        if not evaluation:
            print("DEBUG: No evaluation returned")
            return {
                "score": 0,
                "feedback": "Erreur lors de l'évaluation",
                "educational_content": "Erreur technique lors de l'évaluation.",
            }

        # Generate educational content
        print("DEBUG: Generating educational content...")
        educational_content = client.generate_educational_content(
            recommendation=question_data["recommendation"],
            user_score=evaluation["score"],
        )
        print(
            f"DEBUG: Educational content generated: {educational_content[:100] if educational_content else 'None'}..."
        )

        result = {
            "score": evaluation["score"],
            "feedback": evaluation["feedback"],
            "educational_content": educational_content
            or "Contenu éducatif non disponible",
            "recommendation": question_data["recommendation"],
        }
        print(f"DEBUG: Final result: {result}")
        return result

    except Exception as e:
        print(f"DEBUG: Exception in evaluate_answer: {e}")
        import traceback

        traceback.print_exc()
        return {
            "score": 0,
            "feedback": f"Erreur lors de l'évaluation: {str(e)}",
            "educational_content": "Erreur technique lors de l'évaluation.",
        }


def get_score_category(score: float) -> str:
    """Get descriptive category for a score."""
    if score >= 4.5:
        return "Excellent"
    elif score >= 3.75:
        return "Très bien"
    elif score >= 3:
        return "Bien"
    elif score >= 2:
        return "Moyen"
    else:
        return "Insuffisant"


def calculate_total_score(individual_scores: list) -> Dict:
    """Calculate total score and statistics from individual question scores."""
    if not individual_scores:
        return {
            "total_score": 0,
            "average_score": 0,
            "max_possible": 0,
            "percentage": 0,
            "category": "Aucun score",
        }

    total = sum(individual_scores)
    max_possible = len(individual_scores) * 5
    average = total / len(individual_scores)
    percentage = (total / max_possible) * 100 if max_possible > 0 else 0

    return {
        "total_score": total,
        "average_score": round(average, 1),
        "max_possible": max_possible,
        "percentage": round(percentage, 1),
        "category": get_score_category(average),
        "question_count": len(individual_scores),
    }
