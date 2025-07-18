from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from app.utils.constants import TEAM_LIST, QUESTION_COUNT
from app.utils.vignette import generate_vignette_and_question
from app.utils.scorer import evaluate_answer, calculate_total_score
from app.utils.scoreboard import scoreboard

national_bp = Blueprint("national", __name__)


@national_bp.route("/")
def index():
    """National contest landing page with team selection."""
    return render_template("national/index.html", teams=TEAM_LIST)


@national_bp.route("/select_team", methods=["POST"])
def select_team():
    """Handle team selection and start national quiz."""
    team = request.form.get("team")
    if not team or team not in TEAM_LIST:
        flash("Veuillez sélectionner une équipe valide", "error")
        return redirect(url_for("national.index"))

    # Initialize session for national contest
    session["contest_type"] = "national"
    session["team"] = team
    session["current_question"] = 0
    session["questions"] = []
    session["answers"] = []
    session["scores"] = []

    return redirect(url_for("national.quiz"))


@national_bp.route("/quiz")
def quiz():
    """Display current quiz question."""
    if "team" not in session or session.get("contest_type") != "national":
        flash("Veuillez d'abord sélectionner votre équipe", "error")
        return redirect(url_for("national.index"))

    current_q = session.get("current_question", 0)
    print(f"DEBUG: Loading quiz question {current_q}")
    print(f"DEBUG: Questions in session: {len(session.get('questions', []))}")

    # Check if quiz is complete
    if current_q >= QUESTION_COUNT:
        print(f"DEBUG: Quiz complete, redirecting to results")
        return redirect(url_for("national.results"))

    # Generate new question if needed
    if len(session["questions"]) <= current_q:
        print(f"DEBUG: Generating new question for index {current_q}")
        question_data = generate_vignette_and_question()
        if not question_data:
            flash("Erreur lors de la génération de la question", "error")
            return redirect(url_for("national.index"))

        print(f"DEBUG: Generated question data keys: {question_data.keys()}")
        # Store complete question data with expanded session size
        session["questions"].append(question_data)
        session.modified = True

    question = session["questions"][current_q]
    question_number = current_q + 1
    print(
        f"DEBUG: Displaying question {question_number}, question keys: {question.keys()}"
    )

    return render_template(
        "quiz.html",
        question=question,
        question_number=question_number,
        total_questions=QUESTION_COUNT,
        contest_type="national",
        team=session["team"],
    )


@national_bp.route("/submit_answer", methods=["POST"])
def submit_answer():
    """Process submitted answer and show results."""
    if "team" not in session or session.get("contest_type") != "national":
        flash("Session expirée", "error")
        return redirect(url_for("national.index"))

    user_answer = request.form.get("answer", "").strip()
    current_q = session.get("current_question", 0)

    if current_q >= len(session["questions"]):
        flash("Question non trouvée", "error")
        return redirect(url_for("national.quiz"))

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
        contest_type="national",
    )


@national_bp.route("/next_question", methods=["POST"])
def next_question():
    """Move to next question."""
    if "team" not in session or session.get("contest_type") != "national":
        return redirect(url_for("national.index"))

    current_q = session.get("current_question", 0)
    print(f"DEBUG: Moving from question {current_q} to {current_q + 1}")
    print(f"DEBUG: Session questions count: {len(session.get('questions', []))}")
    print(f"DEBUG: Session answers count: {len(session.get('answers', []))}")
    print(f"DEBUG: Session scores count: {len(session.get('scores', []))}")

    session["current_question"] = current_q + 1
    session.modified = True

    return redirect(url_for("national.quiz"))


@national_bp.route("/results")
def results():
    """Show final results and update leaderboard."""
    if "team" not in session or session.get("contest_type") != "national":
        flash("Session expirée", "error")
        return redirect(url_for("national.index"))

    if len(session.get("scores", [])) < QUESTION_COUNT:
        flash("Quiz non terminé", "error")
        return redirect(url_for("national.quiz"))

    # Calculate final score
    final_stats = calculate_total_score(session["scores"])
    team = session["team"]

    # Add to leaderboard
    scoreboard.add_score(team, final_stats["total_score"])

    # Get current leaderboard
    leaderboard = scoreboard.get_top_teams()

    # Clear session
    for key in [
        "contest_type",
        "team",
        "current_question",
        "questions",
        "answers",
        "scores",
    ]:
        session.pop(key, None)

    return render_template(
        "national/results.html",
        final_stats=final_stats,
        team=team,
        leaderboard=leaderboard,
    )


@national_bp.route("/leaderboard")
def leaderboard():
    """Show current leaderboard."""
    top_teams = scoreboard.get_top_teams()
    return render_template("national/leaderboard.html", leaderboard=top_teams)
