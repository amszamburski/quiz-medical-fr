from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from app.utils.constants import TEAM_LIST
from app.utils.vignette import generate_vignette_and_question
from app.utils.scorer import evaluate_answer, calculate_total_score
from app.utils.scoreboard import scoreboard

TOTAL_QUESTIONS = 1

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

    # Clear any existing session data
    for key in list(session.keys()):
        if key not in ['csrf_token', '_flashes']:
            session.pop(key, None)
    
    # Initialize session for national contest
    session["contest_type"] = "national"
    session["team"] = team
    session["quiz_completed"] = False

    return redirect(url_for("national.quiz"))


@national_bp.route("/quiz")
def quiz():
    """Display the single quiz question."""
    if "team" not in session or session.get("contest_type") != "national":
        flash("Veuillez d'abord sélectionner votre équipe", "error")
        return redirect(url_for("national.index"))

    # Check if quiz is already completed
    if session.get("quiz_completed", False):
        return redirect(url_for("national.results"))

    # Generate question if not already in session
    if "question" not in session:
        print(f"DEBUG: Generating quiz question")
        question_data = generate_vignette_and_question()
        if not question_data:
            flash("Erreur lors de la génération de la question", "error")
            return redirect(url_for("national.index"))

        print(f"DEBUG: Generated question data keys: {question_data.keys()}")
        print(f"DEBUG: Question data size: {len(str(question_data))}")
        session["question"] = question_data
        session.modified = True
        print(f"DEBUG: Question stored in session, session keys: {list(session.keys())}")

    question = session["question"]
    print(f"DEBUG: Displaying question, keys: {question.keys()}")
    print(f"DEBUG: Session keys before rendering: {list(session.keys())}")

    return render_template(
        "quiz.html",
        question=question,
        question_number=1,
        total_questions=TOTAL_QUESTIONS,
        contest_type="national",
        team=session["team"],
    )


@national_bp.route("/submit_answer", methods=["POST"])
def submit_answer():
    """Process submitted answer and redirect to results."""
    print(f"DEBUG: submit_answer called")
    print(f"DEBUG: Session keys: {list(session.keys())}")
    print(f"DEBUG: Contest type: {session.get('contest_type')}")
    print(f"DEBUG: Team in session: {'team' in session}")
    
    if "team" not in session or session.get("contest_type") != "national":
        print("DEBUG: Redirecting to index - no team or wrong contest type")
        flash("Session expirée", "error")
        return redirect(url_for("national.index"))

    if "question" not in session:
        print("DEBUG: Redirecting to quiz - no question in session")
        flash("Question non trouvée", "error")
        return redirect(url_for("national.quiz"))

    user_answer = request.form.get("answer", "").strip()
    question_data = session["question"]
    
    print(f"DEBUG: User answer: {user_answer[:50]}...")
    print(f"DEBUG: Question data keys: {question_data.keys()}")
    
    evaluation = evaluate_answer(user_answer, question_data)
    print(f"DEBUG: Evaluation result: {evaluation}")

    if not evaluation:
        print("DEBUG: No evaluation returned, using fallback")
        evaluation = {
            "score": 0,
            "feedback": "Erreur lors de l'évaluation - aucune réponse de l'IA",
            "educational_content": "Erreur technique lors de l'évaluation.",
        }

    # Store results and mark quiz as completed
    session["user_answer"] = user_answer
    session["evaluation"] = evaluation
    session["quiz_completed"] = True
    session.modified = True
    
    print(f"DEBUG: Session updated, showing feedback")
    print(f"DEBUG: Quiz completed flag: {session.get('quiz_completed')}")

    return render_template(
        "result.html",
        evaluation=evaluation,
        question_data=question_data,
        question_number=1,
        total_questions=TOTAL_QUESTIONS,
        contest_type="national",
    )




@national_bp.route("/results")
def results():
    """Show final results and update leaderboard."""
    if "team" not in session or session.get("contest_type") != "national":
        flash("Session expirée", "error")
        return redirect(url_for("national.index"))

    if not session.get("quiz_completed", False):
        flash("Quiz non terminé", "error")
        return redirect(url_for("national.quiz"))

    evaluation = session.get("evaluation")
    if not evaluation:
        flash("Résultats non trouvés", "error")
        return redirect(url_for("national.quiz"))

    # Calculate final score (single question)
    final_stats = calculate_total_score([evaluation["score"]])
    team = session["team"]

    # Add to leaderboard
    scoreboard.add_score(team, final_stats["total_score"])

    # Get current leaderboard
    leaderboard = scoreboard.get_top_teams()

    # Clear session
    for key in [
        "contest_type",
        "team",
        "question",
        "user_answer",
        "evaluation",
        "quiz_completed",
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
    all_teams = scoreboard.get_top_teams(limit=None)
    return render_template("national/leaderboard.html", leaderboard=all_teams)