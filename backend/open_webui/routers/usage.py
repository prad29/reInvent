import os
import json
import logging
from datetime import datetime, date
from typing import Optional, Dict, Any
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from open_webui.utils.auth import get_verified_user
from pydantic import BaseModel

log = logging.getLogger(__name__)

router = APIRouter()

# Import our new usage tracking utilities
from open_webui.utils.usage_tracking import get_user_usage, track_usage

# Configuration
DATA_DIR = os.path.join(os.getcwd(), "data")


class DailyUsageStats(BaseModel):
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_total: int = 0
    cost: float = 0.0
    date: str


class MonthlyUsageStats(BaseModel):
    tokens_total: int = 0
    cost: float = 0.0
    budget: float = 0.0
    remaining: float = 0.0
    percent_used: float = 0.0


class SessionUsageStats(BaseModel):
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_total: int = 0
    cost: float = 0.0


class UsageStatsResponse(BaseModel):
    daily: DailyUsageStats
    monthly: MonthlyUsageStats
    session: SessionUsageStats
    budget_daily: float = 100.0
    budget_monthly: float = 3000.0


def get_daily_stats(user_id: str) -> DailyUsageStats:
    """Get daily usage statistics for a user."""
    today = date.today().isoformat()
    user_data = get_user_usage(user_id)

    daily_stats = user_data.get("daily", {}).get(today, {})

    return DailyUsageStats(
        tokens_input=daily_stats.get('tokens_input', 0),
        tokens_output=daily_stats.get('tokens_output', 0),
        tokens_total=daily_stats.get('tokens_total', 0),
        cost=daily_stats.get('cost', 0.0),
        date=today
    )


def get_monthly_stats(user_id: str, budget_monthly: float = 3000.0) -> MonthlyUsageStats:
    """Get monthly usage statistics for a user."""
    current_month = datetime.now().strftime("%Y-%m")
    user_data = get_user_usage(user_id)

    monthly_stats = user_data.get("monthly", {}).get(current_month, {})
    monthly_cost = monthly_stats.get('cost', 0.0)
    monthly_tokens = monthly_stats.get('tokens_total', 0)

    remaining = max(0.0, budget_monthly - monthly_cost)
    percent_used = (monthly_cost / budget_monthly * 100) if budget_monthly > 0 else 0.0

    return MonthlyUsageStats(
        tokens_total=monthly_tokens,
        cost=monthly_cost,
        budget=budget_monthly,
        remaining=remaining,
        percent_used=percent_used
    )


def get_session_stats(user_id: str, session_id: Optional[str] = None) -> SessionUsageStats:
    """Get current session statistics."""
    user_data = get_user_usage(user_id)
    sessions = user_data.get("sessions", {})

    if session_id and session_id in sessions:
        # Return specific session
        session = sessions[session_id]
        return SessionUsageStats(
            tokens_input=session.get('tokens_input', 0),
            tokens_output=session.get('tokens_output', 0),
            tokens_total=session.get('tokens_total', 0),
            cost=session.get('cost', 0.0)
        )
    elif sessions:
        # Return most recent session
        from datetime import datetime
        most_recent = max(
            sessions.items(),
            key=lambda x: x[1].get('last_updated', x[1].get('started_at', '')),
            default=(None, {})
        )[1]

        return SessionUsageStats(
            tokens_input=most_recent.get('tokens_input', 0),
            tokens_output=most_recent.get('tokens_output', 0),
            tokens_total=most_recent.get('tokens_total', 0),
            cost=most_recent.get('cost', 0.0)
        )
    else:
        # No sessions yet
        return SessionUsageStats(
            tokens_input=0,
            tokens_output=0,
            tokens_total=0,
            cost=0.0
        )


############################
# GetUsageStats
############################

@router.get("/stats", response_model=UsageStatsResponse)
async def get_usage_stats(user=Depends(get_verified_user)):
    """
    Get comprehensive usage statistics for the current user.

    Returns:
    - daily: Today's token usage and costs
    - monthly: Current month's aggregated usage and budget status
    - session: Current session statistics
    - budget_daily: Daily budget limit
    - budget_monthly: Monthly budget limit
    """
    try:
        # Enhanced Context Counter uses email as the key
        user_id = user.email

        # Get statistics
        daily_stats = get_daily_stats(user_id)
        monthly_stats = get_monthly_stats(user_id)
        session_stats = get_session_stats(user_id)

        return UsageStatsResponse(
            daily=daily_stats,
            monthly=monthly_stats,
            session=session_stats,
            budget_daily=100.0,  # Default budget - could be made configurable
            budget_monthly=3000.0
        )

    except Exception as e:
        log.error(f"Error retrieving usage stats for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving usage statistics: {str(e)}"
        )


############################
# GetDailyHistory
############################

@router.get("/history/daily")
async def get_daily_history(
    days: int = 30,
    user=Depends(get_verified_user)
):
    """
    Get historical daily usage for the past N days.

    Parameters:
    - days: Number of days of history to return (default: 30)
    """
    try:
        user_id = user.email
        from datetime import timedelta

        user_data = get_user_usage(user_id)
        daily_data = user_data.get("daily", {})

        # Get last N days
        history = []
        for day_offset in range(days - 1, -1, -1):
            target_date = datetime.now().date() - timedelta(days=day_offset)
            date_str = target_date.isoformat()

            day_stats = daily_data.get(date_str, {})

            history.append({
                'date': date_str,
                'tokens_input': day_stats.get('tokens_input', 0),
                'tokens_output': day_stats.get('tokens_output', 0),
                'tokens_total': day_stats.get('tokens_total', 0),
                'cost': day_stats.get('cost', 0.0)
            })

        return {
            'user_id': user_id,
            'days': days,
            'history': history
        }

    except Exception as e:
        log.error(f"Error retrieving daily history for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving daily history: {str(e)}"
        )


############################
# GetMonthlyHistory
############################

@router.get("/history/monthly")
async def get_monthly_history(
    months: int = 12,
    user=Depends(get_verified_user)
):
    """
    Get historical monthly usage for the past N months.

    Parameters:
    - months: Number of months of history to return (default: 12)
    """
    try:
        user_id = user.email
        user_data = get_user_usage(user_id)
        monthly_data = user_data.get("monthly", {})

        # Get last N months
        history = []
        for month_offset in range(months - 1, -1, -1):
            from dateutil.relativedelta import relativedelta
            target_date = datetime.now() - relativedelta(months=month_offset)
            month_str = target_date.strftime("%Y-%m")

            month_stats = monthly_data.get(month_str, {})
            history.append({
                'month': month_str,
                'tokens_total': month_stats.get('tokens_total', 0),
                'cost': month_stats.get('cost', 0.0)
            })

        return {
            'user_id': user_id,
            'months': months,
            'history': history
        }

    except Exception as e:
        log.error(f"Error retrieving monthly history for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving monthly history: {str(e)}"
        )


############################
# TrackUsage - Manual endpoint for tracking usage
############################

class TrackUsageRequest(BaseModel):
    model: str
    input_tokens: int
    output_tokens: int
    session_id: Optional[str] = None


@router.post("/track")
async def track_usage_endpoint(
    request: TrackUsageRequest,
    user=Depends(get_verified_user)
):
    """
    Manually track token usage.

    This endpoint can be called by other parts of the application
    to track token usage.
    """
    try:
        track_usage(
            user_email=user.email,
            model=request.model,
            input_tokens=request.input_tokens,
            output_tokens=request.output_tokens,
            session_id=request.session_id
        )

        return {
            "success": True,
            "message": "Usage tracked successfully"
        }

    except Exception as e:
        log.error(f"Error tracking usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error tracking usage: {str(e)}"
        )


############################
# ResetDailyUsage
############################

@router.post("/reset/daily")
async def reset_daily_usage(
    target_date: Optional[str] = None,
    user=Depends(get_verified_user)
):
    """
    Reset daily usage statistics for the current user.

    Parameters:
    - target_date: Optional date in YYYY-MM-DD format (defaults to today)
    """
    try:
        user_id = user.email
        reset_date = target_date if target_date else date.today().isoformat()

        daily_costs = safe_read_json(DAILY_COST_FILE, {})

        if user_id in daily_costs:
            if reset_date in daily_costs[user_id]:
                del daily_costs[user_id][reset_date]

                # Write back to file
                os.makedirs(DATA_DIR, exist_ok=True)
                with open(DAILY_COST_FILE, 'w') as f:
                    json.dump(daily_costs, f, indent=2)

                return {
                    'success': True,
                    'message': f'Daily usage reset for {reset_date}',
                    'user_id': user_id,
                    'date': reset_date
                }

        return {
            'success': False,
            'message': 'No data found for the specified date',
            'user_id': user_id,
            'date': reset_date
        }

    except Exception as e:
        log.error(f"Error resetting daily usage for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resetting daily usage: {str(e)}"
        )
