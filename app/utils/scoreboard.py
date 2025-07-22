"""
24-hour team leaderboard system with Redis/SQLite fallback.
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pytz

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class Scoreboard:
    """Manages 24-hour team leaderboard with Redis primary and SQLite fallback."""

    def __init__(self):
        self.timezone = pytz.timezone("Europe/Paris")
        self.redis_client = None
        self.db_path = os.path.join(
            os.path.dirname(__file__), "../../data/leaderboard.db"
        )

        # Try to connect to Redis first
        if REDIS_AVAILABLE:
            self._init_redis()

        # Always initialize SQLite as fallback
        self._init_sqlite()

    def _init_redis(self):
        """Initialize Redis connection."""
        try:
            redis_url = os.getenv("REDIS_URL") or os.getenv("UPSTASH_REDIS_REST_URL")
            if redis_url:
                if "upstash" in redis_url:
                    # Upstash Redis configuration
                    token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
                    if token:
                        from upstash_redis import Redis

                        self.redis_client = Redis(url=redis_url, token=token)
                else:
                    # Regular Redis
                    self.redis_client = redis.from_url(redis_url)

                # Test connection
                self.redis_client.ping()
                print("Redis connection established")
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self.redis_client = None

    def _init_sqlite(self):
        """Initialize SQLite database."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS team_scores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        team_name TEXT NOT NULL,
                        score INTEGER NOT NULL,
                        timestamp TEXT NOT NULL,
                        player_count INTEGER DEFAULT 1
                    )
                """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_team_timestamp
                    ON team_scores(team_name, timestamp)
                """
                )
                conn.commit()
                print("SQLite database initialized")
        except Exception as e:
            print(f"SQLite initialization failed: {e}")

    def _get_current_day_key(self) -> str:
        """Get Redis key for current day leaderboard."""
        now = datetime.now(self.timezone)
        return f"leaderboard:{now.strftime('%Y-%m-%d')}"

    def _is_today(self, timestamp_str: str) -> bool:
        """Check if timestamp is from today."""
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            timestamp = timestamp.astimezone(self.timezone)
            today = datetime.now(self.timezone).date()
            return timestamp.date() == today
        except:
            return False

    def add_score(self, team_name: str, score: int) -> bool:
        """Add a score to the leaderboard."""
        timestamp = datetime.now(self.timezone).isoformat()

        # Try Redis first
        if self.redis_client:
            try:
                key = self._get_current_day_key()
                # Increment team score and player count
                self.redis_client.hincrby(f"{key}:scores", team_name, score)
                self.redis_client.hincrby(f"{key}:counts", team_name, 1)
                # Set expiration for 25 hours (allows for timezone differences)
                self.redis_client.expire(f"{key}:scores", 25 * 3600)
                self.redis_client.expire(f"{key}:counts", 25 * 3600)
                print(f"Score added to Redis: {team_name} = {score}")
                return True
            except Exception as e:
                print(f"Redis add_score failed: {e}")

        # Fallback to SQLite
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO team_scores (team_name, score, timestamp) VALUES (?, ?, ?)",
                    (team_name, score, timestamp),
                )
                conn.commit()
                print(f"Score added to SQLite: {team_name} = {score}")
                return True
        except Exception as e:
            print(f"SQLite add_score failed: {e}")
            return False

    def get_top_teams(self, limit: int = 3) -> List[Dict]:
        """Get top teams for today's leaderboard."""
        # Try Redis first
        if self.redis_client:
            try:
                key = self._get_current_day_key()
                scores = self.redis_client.hgetall(f"{key}:scores")
                counts = self.redis_client.hgetall(f"{key}:counts")

                if scores:
                    leaderboard = []
                    for team, total_score in scores.items():
                        if isinstance(team, bytes):
                            team = team.decode("utf-8")
                        if isinstance(total_score, bytes):
                            total_score = int(total_score.decode("utf-8"))
                        else:
                            total_score = int(total_score)

                        player_count = 1
                        if team in counts:
                            count_val = counts[team]
                            if isinstance(count_val, bytes):
                                player_count = int(count_val.decode("utf-8"))
                            else:
                                player_count = int(count_val)

                        average_score = (
                            total_score / player_count if player_count > 0 else 0
                        )

                        leaderboard.append(
                            {
                                "team_name": team,
                                "total_score": total_score,
                                "average_score": round(average_score, 1),
                                "player_count": player_count,
                            }
                        )

                    # Sort by average score descending
                    leaderboard.sort(key=lambda x: x["average_score"], reverse=True)
                    
                    return leaderboard[:limit] if limit else leaderboard
            except Exception as e:
                print(f"Redis get_top_teams failed: {e}")

        # Fallback to SQLite
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get today's scores
                today = datetime.now(self.timezone).date().isoformat()
                if limit:
                    cursor = conn.execute(
                        """
                        SELECT team_name, SUM(score) as total_score, COUNT(*) as player_count,
                               ROUND(CAST(SUM(score) AS FLOAT) / CAST(COUNT(*) AS FLOAT), 1) as average_score
                        FROM team_scores
                        WHERE DATE(timestamp) = DATE(?)
                        GROUP BY team_name
                        ORDER BY average_score DESC
                        LIMIT ?
                    """,
                        (today, limit),
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT team_name, SUM(score) as total_score, COUNT(*) as player_count,
                               ROUND(CAST(SUM(score) AS FLOAT) / CAST(COUNT(*) AS FLOAT), 1) as average_score
                        FROM team_scores
                        WHERE DATE(timestamp) = DATE(?)
                        GROUP BY team_name
                        ORDER BY average_score DESC
                    """,
                        (today,),
                    )

                results = []
                for row in cursor.fetchall():
                    team_name, total_score, player_count, average_score = row
                    results.append(
                        {
                            "team_name": team_name,
                            "total_score": total_score,
                            "average_score": average_score,
                            "player_count": player_count,
                        }
                    )

                return results
        except Exception as e:
            print(f"SQLite get_top_teams failed: {e}")
            return []

    def reset_daily_scores(self):
        """Reset daily scores (called automatically by Redis expiration or manually)."""
        if self.redis_client:
            try:
                # Redis handles this automatically with expiration
                pass
            except Exception as e:
                print(f"Redis reset failed: {e}")

        # For SQLite, we can clean up old scores periodically
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Keep only last 7 days of data
                cutoff_date = (
                    datetime.now(self.timezone) - timedelta(days=7)
                ).isoformat()
                conn.execute(
                    "DELETE FROM team_scores WHERE timestamp < ?", (cutoff_date,)
                )
                conn.commit()
        except Exception as e:
            print(f"SQLite cleanup failed: {e}")


# Global scoreboard instance
scoreboard = Scoreboard()