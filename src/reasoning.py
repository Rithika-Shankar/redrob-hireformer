from src.signals import summarize_recruitability
from src.evidence_graph import summarize_evidence_nodes


def clean_name(name):
    return name.replace("_", " ")


def top_dimensions(result, n=2):
    vector = result.get("candidate_vector", {})
    ordered = sorted(vector.items(), key=lambda x: x[1], reverse=True)
    return [clean_name(name) for name, score in ordered[:n] if score > 0]


def get_basic_facts(candidate):
    profile = candidate.get("profile", {})
    return {
        "title": profile.get("current_title", "candidate"),
        "years": profile.get("years_of_experience", 0),
    }


def get_relevant_skills(candidate, blueprint=None, limit=4):
    skills = candidate.get("skills", [])

    if blueprint:
        jd_terms = (
            blueprint.required_skills
            + blueprint.preferred_skills
            + blueprint.responsibilities
            + blueprint.behavioral_traits
        )
    else:
        jd_terms = []

    selected = []

    for skill in skills:
        name = skill.get("name", "")
        name_lower = name.lower()

        if any(term.lower() in name_lower or name_lower in term.lower() for term in jd_terms):
            selected.append(name)

    if not selected:
        selected = [s.get("name", "") for s in skills if s.get("name")]

    return selected[:limit]


def generate_reasoning(candidate, result):
    facts = get_basic_facts(candidate)
    dimensions = top_dimensions(result)
    skills = get_relevant_skills(candidate, result.get("blueprint"))
    evidence_nodes = result.get("evidence_nodes", [])
    evidence_labels = summarize_evidence_nodes(evidence_nodes, limit=2)
    risk_flags = result.get("risk_flags", [])

    title = facts["title"]
    years = facts["years"]

    parts = []

    if dimensions:
        parts.append(
            f"{title} with {years} years of experience aligns strongly with "
            f"{' and '.join(dimensions)} for the Senior AI Engineer role"
        )
    else:
        parts.append(
            f"{title} with {years} years of experience has limited direct alignment with the Senior AI Engineer role"
        )

    if evidence_labels:
        parts.append(
            "evidence graph highlights " + " and ".join(evidence_labels)
        )
    elif skills:
        parts.append(
            "profile lists JD-relevant skills such as " + ", ".join(skills)
        )

    if risk_flags:
        parts.append("concerns: " + "; ".join(risk_flags[:2]))
    else:
        parts.append(
            "hiring panel consensus is supported by " + summarize_recruitability(candidate)
        )

    return (". ".join(parts) + ".")[:450]