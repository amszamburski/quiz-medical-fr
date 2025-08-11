from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
from app.utils.constants import TEAM_LIST
from app.utils.vignette import generate_vignette_and_question
from app.utils.scorer import evaluate_answer, calculate_total_score
from app.utils.scoreboard import scoreboard
from app.utils.session_storage import session_storage
import uuid
import json
import pytz

TOTAL_QUESTIONS = 1

national_bp = Blueprint("national", __name__)


def _paris_today_str():
    tz = pytz.timezone("Europe/Paris")
    return datetime.now(tz).strftime("%Y-%m-%d")


def _daily_question_key():
    return f"national:question:{_paris_today_str()}"


def _get_or_create_daily_question():
    rc = session_storage.redis_client
    key = _daily_question_key()
    # Try fetch existing
    if rc:
        try:
            raw = rc.get(key)
            if raw:
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                return json.loads(raw)
        except Exception as e:
            print(f"WARNING: read daily question failed: {e}")

    # Generate a new shared question
    q = generate_vignette_and_question()
    if not q:
        return None
    if rc:
        try:
            rc.setex(key, 26 * 3600, json.dumps(q, default=str))
            # Best-effort cleanup of yesterday
            try:
                tz = pytz.timezone("Europe/Paris")
                yday = (datetime.now(tz) - timedelta(days=1)).strftime("%Y-%m-%d")
                rc.delete(f"national:question:{yday}")
            except Exception:
                pass
        except Exception as e:
            print(f"WARNING: store daily question failed: {e}")
    return q


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
    
    # Generate unique session ID for this quiz
    quiz_session_id = str(uuid.uuid4())
    
    # Initialize session for national contest
    session.permanent = True  # Make session persistent
    session["contest_type"] = "national"
    session["team"] = team
    session["quiz_completed"] = False
    session["quiz_session_id"] = quiz_session_id

    return redirect(url_for("national.quiz_loading"))


@national_bp.route("/quiz")
def quiz():
    """Display the single quiz question."""
    if "team" not in session or session.get("contest_type") != "national":
        flash("Veuillez d'abord sélectionner votre équipe", "error")
        return redirect(url_for("national.index"))

    # Check if quiz is already completed
    if session.get("quiz_completed", False):
        return redirect(url_for("national.results"))

    # Ensure session id exists
    quiz_session_id = session.get("quiz_session_id")
    if not quiz_session_id:
        flash("Session invalide, veuillez recommencer", "error")
        return redirect(url_for("national.index"))

    # Use the daily shared question
    question = _get_or_create_daily_question()
    if not question:
        flash("Erreur lors de la préparation de la question du jour", "error")
        return redirect(url_for("national.index"))
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


@national_bp.route("/quiz_loading")
def quiz_loading():
    """Loading screen shown while preparing quiz data via OpenAI."""
    if "team" not in session or session.get("contest_type") != "national":
        flash("Veuillez d'abord sélectionner votre équipe", "error")
        return redirect(url_for("national.index"))
    return render_template("national/loading.html")


@national_bp.route("/quiz_prepare")
def quiz_prepare():
    """Prepare quiz data (idempotent). Returns JSON status."""
    if "team" not in session or session.get("contest_type") != "national":
        return jsonify({"ok": False, "error": "invalid_session"}), 400

    try:
        if _get_or_create_daily_question() is None:
            return jsonify({"ok": False, "error": "generation_failed"}), 500
        return jsonify({"ok": True, "status": "ready"})
    except Exception as e:
        print(f"ERROR: quiz_prepare failed: {e}")
        return jsonify({"ok": False, "error": "exception"}), 500


@national_bp.route("/submit_answer", methods=["POST"])
def submit_answer():
    """Process submitted answer and redirect to results."""
    print(f"DEBUG: submit_answer called")
    print(f"DEBUG: Session keys: {list(session.keys())}")
    print(f"DEBUG: Session size estimate: {len(str(dict(session)))} bytes")
    print(f"DEBUG: Contest type: {session.get('contest_type')}")
    print(f"DEBUG: Team in session: {'team' in session}")
    
    if "team" not in session or session.get("contest_type") != "national":
        print("DEBUG: Redirecting to index - no team or wrong contest type")
        flash("Session expirée", "error")
        return redirect(url_for("national.index"))

    # Get today's question and session id
    quiz_session_id = session.get("quiz_session_id")
    question_data = _get_or_create_daily_question()
    if not quiz_session_id or not question_data:
        flash("Session expirée - veuillez recommencer", "error")
        return redirect(url_for("national.index"))

    user_answer = request.form.get("answer", "").strip()
    
    print(f"DEBUG: User answer: {user_answer[:50]}...")
    print(f"DEBUG: Question data keys: {question_data.keys()}")
    
    evaluation = evaluate_answer(user_answer, question_data)
    print(f"DEBUG: Evaluation result: {evaluation}")

    if not evaluation:
        print("DEBUG: No evaluation returned, using fallback")
        evaluation = {
            "score": 0,
            "feedback": "Erreur lors de l'évaluation - aucune réponse de l'IA",
        }

    # Store results for this session (do not modify shared question key)
    store = {"question": question_data, "user_answer": user_answer, "evaluation": evaluation}
    if not session_storage.update_quiz_data(quiz_session_id, store):
        print("WARNING: Failed to update quiz results in Redis")
    
    session["quiz_completed"] = True
    session.modified = True
    
    print(f"DEBUG: Results stored in Redis, showing feedback")
    print(f"DEBUG: Quiz completed flag: {session.get('quiz_completed')}")
    print(f"DEBUG: Evaluation stored in Redis: {store.get('evaluation') is not None}")
    print(f"DEBUG: Session keys after update: {list(session.keys())}")

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
    print(f"DEBUG: Results route accessed")
    print(f"DEBUG: Session keys in results: {list(session.keys())}")
    print(f"DEBUG: Session size in results: {len(str(dict(session)))} bytes")
    print(f"DEBUG: Quiz completed in results: {session.get('quiz_completed')}")
    print(f"DEBUG: Evaluation exists in results: {session.get('evaluation') is not None}")
    
    if "team" not in session or session.get("contest_type") != "national":
        flash("Session expirée", "error")
        return redirect(url_for("national.index"))

    if not session.get("quiz_completed", False):
        flash("Quiz non terminé", "error")
        return redirect(url_for("national.quiz"))

    # Get evaluation from Redis storage
    quiz_session_id = session.get("quiz_session_id")
    quiz_data = session_storage.get_quiz_data(quiz_session_id) if quiz_session_id else None
    
    if not quiz_session_id or not quiz_data:
        print("DEBUG: No quiz session ID or quiz data not found in Redis")
        flash("Session expirée", "error")
        return redirect(url_for("national.index"))
    
    evaluation = quiz_data.get("evaluation")
    if not evaluation:
        print("DEBUG: No evaluation found in Redis - redirecting to quiz")
        flash("Résultats non trouvés", "error")
        return redirect(url_for("national.quiz"))

    # Calculate final score (single question)
    final_stats = calculate_total_score([evaluation["score"]])
    team = session["team"]

    # Add to leaderboard
    scoreboard.add_score(team, final_stats["total_score"])

    # Get current leaderboard
    leaderboard = scoreboard.get_top_teams()

    # Clean up quiz cache
    quiz_session_id = session.get("quiz_session_id")
    # Clean up Redis session data
    if quiz_session_id:
        session_storage.delete_quiz_data(quiz_session_id)
        print(f"DEBUG: Cleaned up Redis data for session {quiz_session_id[:8]}...")

    # Clear session
    for key in [
        "contest_type",
        "team",
        "quiz_session_id",
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


@national_bp.route("/clear_session")
def clear_session():
    """Clear session for debugging - remove in production."""
    session.clear()
    flash("Session cleared", "info")
    return redirect(url_for("main.index"))
