from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from app.utils.constants import QUESTION_COUNT
from app.utils.db import list_topics
from app.utils.vignette import generate_vignette_and_question
from app.utils.scorer import evaluate_answer, calculate_total_score
from app.utils.session_storage import session_storage
import uuid

personal_bp = Blueprint("personal", __name__)


@personal_bp.route("/")
def index():
    """Personal contest landing page with topic selection."""
    topics = list_topics()
    return render_template("personal/index.html", topics=topics)


@personal_bp.route("/select_topic", methods=["POST"])
def select_topic():
    """Handle topic selection (one or many) and start personal quiz."""
    selected = request.form.getlist("topics") or []
    available_topics = set(list_topics())

    # Validate
    selected = [t for t in selected if t in available_topics]
    if not selected:
        flash("Veuillez sélectionner au moins un sujet valide", "error")
        return redirect(url_for("personal.index"))

    # Create a server-side quiz session and minimal client session
    quiz_session_id = str(uuid.uuid4())
    session.permanent = True
    session["contest_type"] = "personal"
    session["quiz_session_id"] = quiz_session_id

    quiz_data = {
        "topics": selected,
        "current_question": 0,
        "questions": [],
        "answers": [],
        "scores": [],
    }

    if not session_storage.store_quiz_data(quiz_session_id, quiz_data):
        flash("Erreur de stockage de session", "error")
        return redirect(url_for("personal.index"))

    return redirect(url_for("personal.quiz"))


@personal_bp.route("/quiz")
def quiz():
    """Display current quiz question (server-side state in Redis/KV)."""
    if session.get("contest_type") != "personal":
        flash("Veuillez d'abord sélectionner votre/vos sujet(s)", "error")
        return redirect(url_for("personal.index"))

    quiz_session_id = session.get("quiz_session_id")
    if not quiz_session_id:
        flash("Session invalide, veuillez recommencer", "error")
        return redirect(url_for("personal.index"))

    quiz_data = session_storage.get_quiz_data(quiz_session_id)
    if not quiz_data:
        flash("Session expirée, veuillez recommencer", "error")
        return redirect(url_for("personal.index"))

    current_q = quiz_data.get("current_question", 0)

    # Generate new question if needed
    if len(quiz_data["questions"]) <= current_q:
        import random
        topics = quiz_data.get("topics", [])
        topic = random.choice(topics) if topics else None
        question_data = generate_vignette_and_question(topic=topic)
        if not question_data:
            flash("Erreur lors de la génération de la question", "error")
            return redirect(url_for("personal.index"))
        quiz_data["questions"].append(question_data)
        if not session_storage.update_quiz_data(quiz_session_id, quiz_data):
            flash("Erreur lors de la mise à jour de la session", "error")
            return redirect(url_for("personal.index"))

    question = quiz_data["questions"][current_q]
    question_number = current_q + 1

    return render_template(
        "quiz.html",
        question=question,
        question_number=question_number,
        total_questions=QUESTION_COUNT,
        contest_type="personal",
        topic=question.get("topic"),
    )


@personal_bp.route("/submit_answer", methods=["POST"])
def submit_answer():
    """Process submitted answer and show results (server-side)."""
    if session.get("contest_type") != "personal":
        flash("Session expirée", "error")
        return redirect(url_for("personal.index"))

    quiz_session_id = session.get("quiz_session_id")
    if not quiz_session_id:
        flash("Session invalide", "error")
        return redirect(url_for("personal.index"))

    quiz_data = session_storage.get_quiz_data(quiz_session_id)
    if not quiz_data:
        flash("Session expirée", "error")
        return redirect(url_for("personal.index"))

    user_answer = request.form.get("answer", "").strip()
    current_q = quiz_data.get("current_question", 0)

    if current_q >= len(quiz_data["questions"]):
        flash("Question non trouvée", "error")
        return redirect(url_for("personal.quiz"))

    # Evaluate answer
    question_data = quiz_data["questions"][current_q]
    evaluation = evaluate_answer(user_answer, question_data)
    if not evaluation:
        evaluation = {
            "score": 0,
            "feedback": "Erreur lors de l'évaluation - aucune réponse de l'IA",
        }

    # Store answer and score in server-side state
    quiz_data["answers"].append(user_answer)
    quiz_data["scores"].append(evaluation["score"])
    session_storage.update_quiz_data(quiz_session_id, quiz_data)

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
    """Move to next question (server-side state)."""
    if session.get("contest_type") != "personal":
        return redirect(url_for("personal.index"))

    quiz_session_id = session.get("quiz_session_id")
    if not quiz_session_id:
        return redirect(url_for("personal.index"))

    quiz_data = session_storage.get_quiz_data(quiz_session_id)
    if not quiz_data:
        return redirect(url_for("personal.index"))

    current_q = quiz_data.get("current_question", 0)
    quiz_data["current_question"] = current_q + 1
    session_storage.update_quiz_data(quiz_session_id, quiz_data)

    return redirect(url_for("personal.quiz"))


@personal_bp.route("/results")
def results():
    """Show final results (server-side state)."""
    if session.get("contest_type") != "personal":
        flash("Session expirée", "error")
        return redirect(url_for("personal.index"))

    quiz_session_id = session.get("quiz_session_id")
    if not quiz_session_id:
        flash("Session invalide", "error")
        return redirect(url_for("personal.index"))

    quiz_data = session_storage.get_quiz_data(quiz_session_id)
    if not quiz_data:
        flash("Session expirée", "error")
        return redirect(url_for("personal.index"))

    scores = quiz_data.get("scores", [])
    answers_count = len(scores)
    mean_score = round(sum(scores) / answers_count, 1) if answers_count else 0
    topics = quiz_data.get("topics", [])

    # Clear server-side state and session keys
    session_storage.delete_quiz_data(quiz_session_id)
    for key in ["contest_type", "quiz_session_id"]:
        session.pop(key, None)

    return render_template(
        "personal/results.html", mean_score=mean_score, answers_count=answers_count, topics=topics
    )
