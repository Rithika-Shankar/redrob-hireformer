from datetime import datetime


REFERENCE_DATE = datetime(2026, 6, 1)


def clamp(value, low, high):
    return max(low, min(high, value))


def days_since(date_str):
    if not date_str:
        return 999

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return max(0, (REFERENCE_DATE - dt).days)
    except ValueError:
        return 999


def score_recency(last_active_date):
    days = days_since(last_active_date)

    if days <= 14:
        return 1.0
    if days <= 30:
        return 0.9
    if days <= 60:
        return 0.75
    if days <= 120:
        return 0.55
    return 0.35


def score_response_rate(rate):
    if rate is None:
        return 0.5
    return clamp(float(rate), 0.0, 1.0)


def score_response_time(hours):
    if hours is None:
        return 0.6

    hours = float(hours)

    if hours <= 24:
        return 1.0
    if hours <= 72:
        return 0.85
    if hours <= 120:
        return 0.65
    if hours <= 168:
        return 0.45
    return 0.3


def score_notice_period(days):
    if days is None:
        return 0.7

    days = int(days)

    if days <= 30:
        return 1.0
    if days <= 60:
        return 0.8
    if days <= 90:
        return 0.6
    if days <= 120:
        return 0.45
    return 0.3


def compute_recruitability_multiplier(candidate):
    signals = candidate.get("redrob_signals", {})

    recency = score_recency(signals.get("last_active_date"))
    response_rate = score_response_rate(signals.get("recruiter_response_rate"))
    response_time = score_response_time(signals.get("avg_response_time_hours"))
    notice = score_notice_period(signals.get("notice_period_days"))

    open_to_work = 1.0 if signals.get("open_to_work_flag") else 0.75
    relocate = 1.0 if signals.get("willing_to_relocate") else 0.75

    interview_completion = signals.get("interview_completion_rate")
    if interview_completion is None:
        interview_completion = 0.6
    interview_completion = clamp(float(interview_completion), 0.0, 1.0)

    verified_bonus = 0
    if signals.get("verified_email"):
        verified_bonus += 0.03
    if signals.get("verified_phone"):
        verified_bonus += 0.03
    if signals.get("linkedin_connected"):
        verified_bonus += 0.03

    raw = (
        0.20 * recency +
        0.20 * response_rate +
        0.15 * response_time +
        0.15 * notice +
        0.10 * open_to_work +
        0.10 * relocate +
        0.10 * interview_completion
    )

    multiplier = raw + verified_bonus

    return clamp(multiplier, 0.50, 1.05)


def summarize_recruitability(candidate):
    signals = candidate.get("redrob_signals", {})

    notes = []

    if signals.get("open_to_work_flag"):
        notes.append("open to work")
    else:
        notes.append("not marked open to work")

    if signals.get("willing_to_relocate"):
        notes.append("willing to relocate")
    else:
        notes.append("not relocation-ready")

    notice = signals.get("notice_period_days")
    if notice is not None:
        notes.append(f"{notice}-day notice period")

    response_rate = signals.get("recruiter_response_rate")
    if response_rate is not None:
        notes.append(f"{round(response_rate * 100)}% recruiter response rate")

    return ", ".join(notes)