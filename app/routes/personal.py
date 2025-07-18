from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from app.utils.constants import QUESTION_COUNT
from app.utils.db import list_topics
from app.utils.vignette import generate_vignette_and_question
from app.utils.scorer import evaluate_answer, calculate_total_score

personal_bp = Blueprint("personal", __name__)


@personal_bp.route("/")
def index():
    """Personal contest landing page with topic selection."""
    topics = list_topics()
    return render_template("personal/index.html", topics=topics)


@personal_bp.route("/select_topic", methods=["POST"])
def select_topic():
    """Handle topic selection and start personal quiz."""
    topic = request.form.get("topic")
    available_topics = list_topics()

    if not topic or topic not in available_topics:
        flash("Veuillez sélectionner un sujet valide", "error")
        return redirect(url_for("personal.index"))

    # Initialize session for personal contest
    session["contest_type"] = "personal"
    session["topic"] = topic
    session["current_question"] = 0
    session["questions"] = []
    session["answers"] = []
    session["scores"] = []

    return redirect(url_for("personal.quiz"))


@personal_bp.route("/quiz")
def quiz():
    """Display current quiz question."""
    if "topic" not in session or session.get("contest_type") != "personal":
        flash("Veuillez d'abord sélectionner votre sujet", "error")
        return redirect(url_for("personal.index"))

    current_q = session.get("current_question", 0)

    # Check if quiz is complete
    if current_q >= QUESTION_COUNT:
        return redirect(url_for("personal.results"))

    # Generate new question if needed
    if len(session["questions"]) <= current_q:
        topic = session["topic"]
        question_data = generate_vignette_and_question(topic=topic)
        if not question_data:
            flash(
                f"Erreur lors de la génération de la question pour le sujet {topic}",
                "error",
            )
            return redirect(url_for("personal.index"))

        # Store complete question data with expanded session size
        session["questions"].append(question_data)
        session.modified = True

    question = session["questions"][current_q]
    question_number = current_q + 1

    return render_template(
        "quiz.html",
        question=question,
        question_number=question_number,
        total_questions=QUESTION_COUNT,
        contest_type="personal",
        topic=session["topic"],
    )


@personal_bp.route("/submit_answer", methods=["POST"])
def submit_answer():
    """Process submitted answer and show results."""
    if "topic" not in session or session.get("contest_type") != "personal":
        flash("Session expirée", "error")
        return redirect(url_for("personal.index"))

    user_answer = request.form.get("answer", "").strip()
    current_q = session.get("current_question", 0)

    if current_q >= len(session["questions"]):
        flash("Question non trouvée", "error")
        return redirect(url_for("personal.quiz"))

    # Evaluate answer
    question_data = session["questions"][current_q]
    print(f"DEBUG: Evaluating answer: {user_answer[:50]}...")  # Debug log
    print(f"DEBUG: Question data keys: {question_data.keys()}")  # Debug log
    evaluation = evaluate_answer(user_answer, question_data)
    print(f"DEBUG: Evaluation result: {evaluation}")  # Debug log

    if not evaluation:
        print("DEBUG: No evaluation returned, using fallback")
        evaluation = {
            "score": 0,
            "score_letter": "C",
            "feedback": "Erreur lors de l'évaluation - aucune réponse de l'IA",
            "educational_content": "Erreur technique lors de l'évaluation.",
        }

    # Store answer and score with expanded session size
    session["answers"].append(user_answer)
    session["scores"].append(evaluation["score"])
    session.modified = True

    return render_template(
        "result.html",
        evaluation=evaluation,
        question_data=question_data,
        question_number=current_q + 1,
        total_questions=QUESTION_COUNT,
        contest_type="personal",
    )


@personal_bp.route("/next_question", methods=["POST"])
def next_question():
    """Move to next question."""
    if "topic" not in session or session.get("contest_type") != "personal":
        return redirect(url_for("personal.index"))

    current_q = session.get("current_question", 0)
    print(f"DEBUG: Moving from question {current_q} to {current_q + 1}")
    print(f"DEBUG: Session questions count: {len(session.get('questions', []))}")
    print(f"DEBUG: Session answers count: {len(session.get('answers', []))}")
    print(f"DEBUG: Session scores count: {len(session.get('scores', []))}")

    session["current_question"] = current_q + 1
    session.modified = True

    return redirect(url_for("personal.quiz"))


@personal_bp.route("/results")
def results():
    """Show final results."""
    if "topic" not in session or session.get("contest_type") != "personal":
        flash("Session expirée", "error")
        return redirect(url_for("personal.index"))

    if len(session.get("scores", [])) < QUESTION_COUNT:
        flash("Quiz non terminé", "error")
        return redirect(url_for("personal.quiz"))

    # Calculate final score
    final_stats = calculate_total_score(session["scores"])
    topic = session["topic"]

    # Clear session
    for key in [
        "contest_type",
        "topic",
        "current_question",
        "questions",
        "answers",
        "scores",
    ]:
        session.pop(key, None)

    return render_template(
        "personal/results.html", final_stats=final_stats, topic=topic
    )
