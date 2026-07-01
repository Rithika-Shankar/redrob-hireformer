def clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))


def get_vector(result):
    return result.get("candidate_vector", {})


def score_ml_lead(result):
    v = get_vector(result)

    score = (
        0.25 * v.get("retrieval_systems", 0) +
        0.22 * v.get("ranking_systems", 0) +
        0.18 * v.get("evaluation_frameworks", 0) +
        0.18 * v.get("production_ml", 0) +
        0.10 * v.get("python_engineering", 0) +
        0.07 * v.get("llm_depth", 0)
    ) * 100

    return clamp(score)


def score_recruiter(result):
    candidate = result["candidate"]
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    years = float(profile.get("years_of_experience", 0) or 0)

    seniority = 100 if 5 <= years <= 9 else 75 if 4 <= years <= 11 else 45
    availability = 100 if signals.get("open_to_work_flag") else 70
    relocation = 100 if signals.get("willing_to_relocate") else 70
    response = float(signals.get("recruiter_response_rate", 0.5) or 0.5) * 100

    notice = int(signals.get("notice_period_days", 90) or 90)
    if notice <= 30:
        notice_score = 100
    elif notice <= 60:
        notice_score = 80
    elif notice <= 90:
        notice_score = 60
    else:
        notice_score = 40

    score = (
        0.30 * seniority +
        0.20 * availability +
        0.20 * relocation +
        0.20 * response +
        0.10 * notice_score
    )

    return clamp(score)


def score_product_lead(result):
    v = get_vector(result)

    score = (
        0.35 * v.get("product_shipper", 0) +
        0.25 * v.get("startup_fit", 0) +
        0.20 * v.get("leadership_mentoring", 0) +
        0.20 * v.get("evidence_strength", 0)
    ) * 100

    return clamp(score)


def score_risk_auditor(result):
    risk_multiplier = result.get("risk_multiplier", 1.0)
    confidence = result.get("confidence", 0.5)
    evidence_nodes = result.get("evidence_nodes", [])

    evidence_score = min(100, len(evidence_nodes) * 18)

    score = (
        0.45 * (risk_multiplier * 100) +
        0.30 * (confidence * 100) +
        0.25 * evidence_score
    )

    return clamp(score)


def compute_panel_scores(result):
    panel = {
        "ml_lead": round(score_ml_lead(result), 3),
        "recruiter": round(score_recruiter(result), 3),
        "product_lead": round(score_product_lead(result), 3),
        "risk_auditor": round(score_risk_auditor(result), 3),
    }

    consensus = (
        0.42 * panel["ml_lead"] +
        0.22 * panel["recruiter"] +
        0.18 * panel["product_lead"] +
        0.18 * panel["risk_auditor"]
    )

    panel["consensus"] = round(consensus, 6)
    return panel