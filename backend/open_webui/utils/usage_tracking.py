"""
Usage tracking utilities for monitoring token usage and costs across the application.
"""

import os
import json
import logging
from datetime import datetime, date
from typing import Dict, Optional
import fcntl
from contextlib import contextmanager

log = logging.getLogger(__name__)

# Configuration
DATA_DIR = os.path.join(os.getcwd(), "data")
USER_USAGE_FILE = os.path.join(DATA_DIR, "user_usage.json")

# Model pricing (per million tokens)
MODEL_PRICING = {
    "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
    "claude-sonnet-3-5": {"input": 3.0, "output": 15.0},
    "claude-opus-4": {"input": 15.0, "output": 75.0},
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    # Add more models as needed
}


@contextmanager
def locked_json_file(file_path: str, mode: str = 'r+'):
    """Context manager for thread-safe JSON file access with file locking."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Create file if it doesn't exist
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump({}, f)

    file = open(file_path, mode)
    try:
        fcntl.flock(file.fileno(), fcntl.LOCK_EX)
        yield file
    finally:
        fcntl.flock(file.fileno(), fcntl.LOCK_UN)
        file.close()


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate the cost based on model and token counts."""
    # Extract base model name (remove version suffixes)
    base_model = model.lower()
    for known_model in MODEL_PRICING.keys():
        if known_model in base_model:
            pricing = MODEL_PRICING[known_model]
            input_cost = (input_tokens / 1_000_000) * pricing["input"]
            output_cost = (output_tokens / 1_000_000) * pricing["output"]
            return input_cost + output_cost

    # Default pricing if model not found
    log.warning(f"Unknown model {model}, using default pricing")
    return ((input_tokens / 1_000_000) * 3.0) + ((output_tokens / 1_000_000) * 15.0)


def track_usage(
    user_email: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    session_id: Optional[str] = None
):
    """
    Track token usage for a user.

    Args:
        user_email: User's email address
        model: Model name/ID
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        session_id: Optional session identifier
    """
    try:
        cost = calculate_cost(model, input_tokens, output_tokens)
        timestamp = datetime.now().isoformat()
        today = date.today().isoformat()
        current_month = datetime.now().strftime("%Y-%m")

        with locked_json_file(USER_USAGE_FILE, 'r+') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}

            # Initialize user data if not exists
            if user_email not in data:
                data[user_email] = {
                    "daily": {},
                    "monthly": {},
                    "sessions": {},
                    "history": []
                }

            user_data = data[user_email]

            # Update daily stats
            if today not in user_data["daily"]:
                user_data["daily"][today] = {
                    "tokens_input": 0,
                    "tokens_output": 0,
                    "tokens_total": 0,
                    "cost": 0.0
                }

            user_data["daily"][today]["tokens_input"] += input_tokens
            user_data["daily"][today]["tokens_output"] += output_tokens
            user_data["daily"][today]["tokens_total"] += input_tokens + output_tokens
            user_data["daily"][today]["cost"] += cost

            # Update monthly stats
            if current_month not in user_data["monthly"]:
                user_data["monthly"][current_month] = {
                    "tokens_total": 0,
                    "cost": 0.0
                }

            user_data["monthly"][current_month]["tokens_total"] += input_tokens + output_tokens
            user_data["monthly"][current_month]["cost"] += cost

            # Update session stats if session_id provided
            if session_id:
                if session_id not in user_data["sessions"]:
                    user_data["sessions"][session_id] = {
                        "tokens_input": 0,
                        "tokens_output": 0,
                        "tokens_total": 0,
                        "cost": 0.0,
                        "started_at": timestamp
                    }

                user_data["sessions"][session_id]["tokens_input"] += input_tokens
                user_data["sessions"][session_id]["tokens_output"] += output_tokens
                user_data["sessions"][session_id]["tokens_total"] += input_tokens + output_tokens
                user_data["sessions"][session_id]["cost"] += cost
                user_data["sessions"][session_id]["last_updated"] = timestamp

            # Add to history
            user_data["history"].append({
                "model": model,
                "timestamp": timestamp,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": cost,
                "session_id": session_id
            })

            # Keep only last 1000 history records to prevent file bloat
            if len(user_data["history"]) > 1000:
                user_data["history"] = user_data["history"][-1000:]

            # Write back to file
            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())

        log.info(f"Tracked usage for {user_email}: {input_tokens} in, {output_tokens} out, ${cost:.6f}")

    except Exception as e:
        log.error(f"Error tracking usage for {user_email}: {e}")


def get_user_usage(user_email: str) -> Dict:
    """Get usage data for a specific user."""
    try:
        if not os.path.exists(USER_USAGE_FILE):
            return {
                "daily": {},
                "monthly": {},
                "sessions": {},
                "history": []
            }

        with locked_json_file(USER_USAGE_FILE, 'r') as f:
            data = json.load(f)
            return data.get(user_email, {
                "daily": {},
                "monthly": {},
                "sessions": {},
                "history": []
            })
    except Exception as e:
        log.error(f"Error getting usage for {user_email}: {e}")
        return {
            "daily": {},
            "monthly": {},
            "sessions": {},
            "history": []
        }


def cleanup_old_sessions(user_email: str, keep_days: int = 7):
    """Clean up old session data to prevent file bloat."""
    try:
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=keep_days)

        with locked_json_file(USER_USAGE_FILE, 'r+') as f:
            data = json.load(f)

            if user_email in data and "sessions" in data[user_email]:
                sessions = data[user_email]["sessions"]
                sessions_to_delete = []

                for session_id, session_data in sessions.items():
                    last_updated = session_data.get("last_updated", session_data.get("started_at"))
                    if last_updated:
                        session_date = datetime.fromisoformat(last_updated)
                        if session_date < cutoff_date:
                            sessions_to_delete.append(session_id)

                for session_id in sessions_to_delete:
                    del sessions[session_id]

                # Write back
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=2)

                log.info(f"Cleaned up {len(sessions_to_delete)} old sessions for {user_email}")

    except Exception as e:
        log.error(f"Error cleaning up sessions for {user_email}: {e}")
