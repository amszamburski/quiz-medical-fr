import os
import openai
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Optional, Dict
import re


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

        # Harmonized: force GPT-5 for all API calls
        self.model = "gpt-5"

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def chat_completion(
        self, messages: list, temperature: float = 0.7, max_tokens: int = 4000
    ) -> Optional[str]:
        """Make a completion request (Responses API) with retry logic."""
        try:
            print(
                f"DEBUG: Making OpenAI API call with {len(messages)} messages, max_tokens={max_tokens}"
            )

            # Compile messages into a single input string for the Responses API
            compiled_input = "\n".join(
                f"{m.get('role', 'user').upper()}: {m.get('content', '')}" for m in messages
            )

            response = self.client.responses.create(
                model=self.model,
                input=compiled_input,
                # Use Responses API token parameter name
                max_output_tokens=max_tokens,
                reasoning={"effort": "low"},
                # Omit temperature for GPT-5 to avoid incompatibility
            )

            # Unified text accessor for Responses API
            content = getattr(response, "output_text", None)
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

            response = self.chat_completion(messages, temperature=0.7, max_tokens=4000)
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

            response = self.chat_completion(messages, temperature=0.3, max_tokens=4000)
            if not response:
                print("DEBUG: No response from OpenAI")
                return {
                    "score": 0,
                    "feedback": "Aucune réponse de l'IA - évaluation par défaut",
                }

            # Parse the response to extract score and feedback
            print(f"DEBUG: Raw OpenAI response: {response}")

            # More robust parsing
            score_numeric = None
            feedback = ""

            # Extract score using regex
            score_match = re.search(r'SCORE:\s*(\d)', response)
            if score_match:
                try:
                    score_numeric = int(score_match.group(1))
                    if score_numeric not in range(6):
                        raise ValueError("Score out of range")
                except ValueError:
                    print(f"DEBUG: Invalid score parsed: {score_match.group(1)}. Setting to 0.")
                    score_numeric = 0
            else:
                print("DEBUG: No SCORE found in response. Setting to 0.")
                score_numeric = 0

            # Extract feedback
            if "FEEDBACK:" in response:
                feedback_parts = response.split("FEEDBACK:")
                if len(feedback_parts) > 1:
                    feedback = feedback_parts[1].strip()

            # If no proper parsing, try to extract any useful content
            if not feedback and response:
                # If response doesn't follow format, use the whole response as feedback
                feedback = response.strip()

            print(
                f"DEBUG: Parsed - Score: {score_numeric}, Feedback: {feedback[:100]}..."
            )

            # Ensure we always have some feedback
            if not feedback:
                feedback = "Réponse évaluée. Veuillez consulter le contenu éducatif pour plus de détails."

            return {
                "score": score_numeric if score_numeric is not None else 0,
                "feedback": feedback,
            }

        except Exception as e:
            print(f"Error evaluating answer: {e}")
            import traceback

            traceback.print_exc()
            return {
                "score": 0,
                "feedback": f"Erreur lors de l'évaluation: {str(e)}",
            }



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
        # Mock 0-5 scoring based on answer length and content
        if len(user_answer) > 30 and any(
            word in user_answer.lower()
            for word in ["traitement", "prise en charge", "urgence", "stabilisation"]
        ):
            score = 5  # Excellent
            feedback = f"Excellente réponse. Votre approche est cohérente avec la recommandation {correct_recommendation.get('grade', 'N/A')}. Vous avez bien identifié les éléments clés de la prise en charge."
        elif len(user_answer) > 15:
            score = 3  # Moyen
            feedback = f"Réponse correcte mais incomplète. Vous avez saisi l'essentiel de la recommandation {correct_recommendation.get('grade', 'N/A')}, mais certains détails manquent."
        else:
            score = 1  # Mauvais
            feedback = f"Réponse insuffisante. La recommandation {correct_recommendation.get('grade', 'N/A')} requiert une approche plus complète. Consultez le contenu éducatif."

        return {"score": score, "feedback": feedback}
