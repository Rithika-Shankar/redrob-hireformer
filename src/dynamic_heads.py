from src.text_builder import build_candidate_text


def clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))


def normalize(text):
    return str(text or "").lower()


def count_term_matches(text, terms):
    text = normalize(text)
    score = 0

    for term in terms:
        term = normalize(term)
        if not term:
            continue

        # phrase match
        if term in text:
            score += 1

        # partial important-word match
        important_words = [
            w for w in term.replace("/", " ").replace("-", " ").split()
            if len(w) >= 4
        ]
        for word in important_words:
            if word in text:
                score += 0.35

    return score


def build_dynamic_heads(blueprint):
    """
    Creates evaluation heads from the JD blueprint.
    This is the HireFormer idea:
    the JD creates the attention heads instead of the ranker using fixed heads.
    """

    return [
        {
            "name": "required_skill_alignment",
            "label": "Required Skill Alignment",
            "weight": 0.28,
            "terms": blueprint.required_skills,
            "source": "skills+career",
        },
        {
            "name": "responsibility_alignment",
            "label": "Responsibility Alignment",
            "weight": 0.22,
            "terms": blueprint.responsibilities,
            "source": "career",
        },
        {
            "name": "production_evidence",
            "label": "Production Evidence",
            "weight": 0.18,
            "terms": [
                "production",
                "deployed",
                "real users",
                "monitoring",
                "pipeline",
                "scale",
                "latency",
                "on-call",
                "A/B testing",
                "feedback loops",
                "evaluation infrastructure",
            ],
            "source": "career",
        },
        {
            "name": "preferred_depth",
            "label": "Preferred Technical Depth",
            "weight": 0.12,
            "terms": blueprint.preferred_skills,
            "source": "skills+career",
        },
        {
            "name": "behavioral_fit",
            "label": "Behavioral Fit",
            "weight": 0.10,
            "terms": blueprint.behavioral_traits + blueprint.hidden_expectations,
            "source": "profile+career",
        },
        {
            "name": "evidence_strength",
            "label": "Evidence Strength",
            "weight": 0.10,
            "terms": [
                "built",
                "implemented",
                "designed",
                "owned",
                "maintained",
                "launched",
                "improved",
                "reduced",
                "increased",
                "led",
                "mentored",
                "processed",
                "shipped",
            ],
            "source": "career",
        },
    ]


def score_skill_quality(candidate, terms):
    skills = candidate.get("skills", [])
    score = 0

    for skill in skills:
        name = normalize(skill.get("name"))
        proficiency = normalize(skill.get("proficiency"))
        duration = int(skill.get("duration_months", 0) or 0)
        endorsements = int(skill.get("endorsements", 0) or 0)

        matched = False
        for term in terms:
            term = normalize(term)
            if term in name or name in term:
                matched = True
                break

        if not matched:
            continue

        if proficiency == "expert":
            score += 18
        elif proficiency == "advanced":
            score += 14
        elif proficiency == "intermediate":
            score += 9
        else:
            score += 5

        if duration >= 36:
            score += 6
        elif duration >= 18:
            score += 4
        elif duration >= 6:
            score += 2

        if endorsements >= 30:
            score += 5
        elif endorsements >= 10:
            score += 3

    return score


def get_source_text(candidate, source):
    texts = build_candidate_text(candidate)

    if source == "career":
        return texts["career_text"]
    if source == "skills":
        return texts["skills_text"]
    if source == "profile+career":
        return texts["profile_text"] + "\n" + texts["career_text"]
    if source == "skills+career":
        return texts["skills_text"] + "\n" + texts["career_text"]

    return texts["full_text"]


def score_dynamic_head(candidate, head):
    source_text = get_source_text(candidate, head["source"])
    terms = head["terms"]

    match_score = count_term_matches(source_text, terms)

    # Scale based on number of terms so long JD sections don't unfairly dominate.
    denominator = max(4, min(len(terms), 16))
    normalized_match = (match_score / denominator) * 70

    skill_bonus = 0
    if "skills" in head["source"]:
        skill_bonus = score_skill_quality(candidate, terms) * 0.8

    return clamp(normalized_match + skill_bonus)


def compute_dynamic_head_scores(candidate, blueprint):
    heads = build_dynamic_heads(blueprint)
    scores = {}

    for head in heads:
        scores[head["name"]] = round(score_dynamic_head(candidate, head), 3)

    return scores


def compute_dynamic_base_score(head_scores, blueprint):
    heads = build_dynamic_heads(blueprint)
    total = 0

    for head in heads:
        total += head["weight"] * head_scores.get(head["name"], 0)

    return round(total, 3)