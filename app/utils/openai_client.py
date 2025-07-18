import os
import openai
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Optional, Dict


class OpenAIClient:
    """OpenAI client with retry logic and error handling."""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        # Initialize with basic configuration to avoid compatibility issues
        try:
            self.client = openai.OpenAI(api_key=api_key)
        except Exception as e:
            print(f"OpenAI client initialization failed: {e}")
            raise

        self.model = "gpt-4o"

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def chat_completion(
        self, messages: list, temperature: float = 0.7, max_tokens: int = 1000
    ) -> Optional[str]:
        """Make a chat completion request with retry logic."""
        try:
            print(
                f"DEBUG: Making OpenAI API call with {len(messages)} messages, max_tokens={max_tokens}"
            )
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            print(
                f"DEBUG: OpenAI API response received, length: {len(content) if content else 0}"
            )
            return content
        except Exception as e:
            print(f"OpenAI API error: {e}")
            raise

    def generate_vignette_and_question(self, recommendation: Dict) -> Optional[Dict]:
        """Generate clinical vignette and question from recommendation."""
        try:
            from .prompts import get_vignette_prompt

            messages = [
                {"role": "system", "content": get_vignette_prompt(recommendation)},
                {
                    "role": "user",
                    "content": "Génère maintenant la vignette clinique et la question basées sur cette recommandation.",
                },
            ]

            response = self.chat_completion(messages, temperature=0.8, max_tokens=800)
            if not response:
                return None

            # Parse the response to extract vignette and question
            parts = response.split("QUESTION:")
            if len(parts) != 2:
                return None

            vignette = parts[0].replace("VIGNETTE:", "").strip()
            question = parts[1].strip()

            return {
                "vignette": vignette,
                "question": question,
                "recommendation_id": recommendation.get("id"),
            }

        except Exception as e:
            print(f"Error generating vignette: {e}")
            return None

    def evaluate_answer(
        self,
        user_answer: str,
        correct_recommendation: Dict,
        vignette: str,
        question: str,
    ) -> Optional[Dict]:
        """Evaluate user's answer and provide score and feedback."""
        try:
            from .prompts import get_scoring_prompt

            messages = [
                {
                    "role": "system",
                    "content": get_scoring_prompt(correct_recommendation),
                },
                {
                    "role": "user",
                    "content": f"""
VIGNETTE: {vignette}
QUESTION: {question}
RÉPONSE DE L'UTILISATEUR: {user_answer}
""",
                },
            ]

            response = self.chat_completion(messages, temperature=0.3, max_tokens=1200)
            if not response:
                print("DEBUG: No response from OpenAI")
                return {
                    "score": 6,
                    "score_letter": "C",
                    "feedback": "Aucune réponse de l'IA - évaluation par défaut",
                }

            # Parse the response to extract score and feedback
            print(f"DEBUG: Raw OpenAI response: {response}")

            # More robust parsing
            score_letter = None
            score_numeric = None
            feedback = ""

            # Split by SCORE: and FEEDBACK:
            if "SCORE:" in response:
                parts = response.split("SCORE:")
                if len(parts) > 1:
                    score_part = parts[1].split("FEEDBACK:")[0].strip()
                    score_text = score_part.strip()
                    if score_text == "A":
                        score_letter = "A"
                        score_numeric = 18
                    elif score_text == "B":
                        score_letter = "B"
                        score_numeric = 12
                    elif score_text == "C":
                        score_letter = "C"
                        score_numeric = 6
                    else:
                        score_letter = "C"
                        score_numeric = 0

            if "FEEDBACK:" in response:
                feedback_parts = response.split("FEEDBACK:")
                if len(feedback_parts) > 1:
                    feedback = feedback_parts[1].strip()

            # If no proper parsing, try to extract any useful content
            if not feedback and response:
                # If response doesn't follow format, use the whole response as feedback
                feedback = response.strip()

            print(
                f"DEBUG: Parsed - Score: {score_letter}, Feedback: {feedback[:100]}..."
            )

            # Ensure we always have some feedback
            if not feedback:
                feedback = "Réponse évaluée. Veuillez consulter le contenu éducatif pour plus de détails."

            return {
                "score": score_numeric if score_numeric is not None else 6,
                "score_letter": score_letter or "C",
                "feedback": feedback,
            }

        except Exception as e:
            print(f"Error evaluating answer: {e}")
            import traceback

            traceback.print_exc()
            return {
                "score": 0,
                "score_letter": "C",
                "feedback": f"Erreur lors de l'évaluation: {str(e)}",
            }

    def generate_educational_content(
        self, recommendation: Dict, user_score: int
    ) -> Optional[str]:
        """Generate educational paragraph with evidence and references."""
        try:
            from .prompts import get_educational_prompt

            messages = [
                {
                    "role": "system",
                    "content": get_educational_prompt(recommendation, user_score),
                },
                {
                    "role": "user",
                    "content": "Génère maintenant le contenu éducatif basé sur ces informations.",
                },
            ]

            response = self.chat_completion(messages, temperature=0.5, max_tokens=1000)
            return response

        except Exception as e:
            print(f"Error generating educational content: {e}")
            return "Contenu éducatif non disponible"


# Global client instance (lazy initialization)
openai_client = None


def get_openai_client():
    """Get or create OpenAI client instance."""
    global openai_client
    if openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "dummy-key-for-testing":
            # Return mock client for testing
            openai_client = MockOpenAIClient()
        else:
            # Always use real OpenAI client when API key is available
            openai_client = OpenAIClient()
    return openai_client


class MockOpenAIClient:
    """Mock OpenAI client for testing without API key."""

    def generate_vignette_and_question(self, recommendation):
        """Mock vignette generation."""
        topic = recommendation.get("topic", "condition médicale")
        theme = recommendation.get("theme", "médecine générale")

        return {
            "vignette": f"Patient de 45 ans présentant des symptômes liés à {topic}. Examen clinique et paraclinique en cours. Que recommandez-vous selon les guidelines de {theme} ?",
            "question": f"Quelle est la prise en charge recommandée pour ce patient selon les guidelines actuelles ?\n\nA) Surveillance simple\nB) Traitement médical conservateur\nC) Intervention chirurgicale en urgence\nD) Investigations complémentaires",
        }

    def evaluate_answer(self, user_answer, correct_recommendation, vignette, question):
        """Mock answer evaluation."""
        # Mock A/B/C scoring based on answer length and content
        if len(user_answer) > 30 and any(
            word in user_answer.lower()
            for word in ["traitement", "prise en charge", "urgence", "stabilisation"]
        ):
            score = 18  # Grade A
            grade = "A"
            feedback = f"Excellente réponse. Votre approche est cohérente avec la recommandation {correct_recommendation.get('grade', 'N/A')}. Vous avez bien identifié les éléments clés de la prise en charge."
        elif len(user_answer) > 15:
            score = 12  # Grade B
            grade = "B"
            feedback = f"Réponse correcte mais incomplète. Vous avez saisi l'essentiel de la recommandation {correct_recommendation.get('grade', 'N/A')}, mais certains détails manquent."
        else:
            score = 6  # Grade C
            grade = "C"
            feedback = f"Réponse insuffisante. La recommandation {correct_recommendation.get('grade', 'N/A')} requiert une approche plus complète. Consultez le contenu éducatif."

        return {"score": score, "score_letter": grade, "feedback": feedback}

    def generate_educational_content(self, recommendation, user_score):
        """Mock educational content."""
        return f"Contenu éducatif de démonstration pour {recommendation['topic']}. Score: {user_score}/20. Références: {recommendation.get('references', 'Non disponible')}"
