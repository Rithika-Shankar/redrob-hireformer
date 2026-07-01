from src.hireformer_v3 import compute_v3_scores
from src.signals import compute_recruitability_multiplier
from src.risk_rules import compute_risk_multiplier
from src.hiring_panel import compute_panel_scores


def evaluate_candidate(candidate, blueprint=None):
    v3 = compute_v3_scores(candidate)

    candidate_vector = v3["candidate_vector"]
    confidence = v3["confidence"]
    evidence_nodes = v3["evidence_nodes"]

    recruitability = compute_recruitability_multiplier(candidate)
    risk_multiplier, risk_flags = compute_risk_multiplier(candidate)

    temp_result = {
        "candidate_id": candidate["candidate_id"],
        "candidate_vector": candidate_vector,
        "confidence": confidence,
        "evidence_nodes": evidence_nodes,
        "recruitability_multiplier": round(recruitability, 3),
        "risk_multiplier": round(risk_multiplier, 3),
        "risk_flags": risk_flags,
        "candidate": candidate,
        "blueprint": blueprint,
    }

    panel_scores = compute_panel_scores(temp_result)
    consensus_score = panel_scores["consensus"]

    final_score = consensus_score * recruitability * risk_multiplier

    return {
        **temp_result,
        "score": round(final_score, 6),
        "base_score": round(consensus_score, 3),
        "panel_scores": panel_scores,
        "head_scores": {
            key: round(value * 100, 3)
            for key, value in candidate_vector.items()
        },
    }


def rank_candidates(candidates, blueprint=None):
    results = []

    for candidate in candidates:
        results.append(evaluate_candidate(candidate, blueprint))

    results.sort(key=lambda x: (-x["score"], x["candidate_id"]))

    for idx, result in enumerate(results, start=1):
        result["rank"] = idx

    return results