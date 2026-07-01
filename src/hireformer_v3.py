from src.text_builder import build_candidate_text
from src.evidence_graph import graph_dimension_boost, extract_evidence_graph


DIMENSIONS = [
    "retrieval_systems",
    "ranking_systems",
    "evaluation_frameworks",
    "production_ml",
    "python_engineering",
    "llm_depth",
    "product_shipper",
    "leadership_mentoring",
    "startup_fit",
    "evidence_strength",
]


DIMENSION_TERMS = {
    "retrieval_systems": [
        "embeddings", "retrieval", "semantic search", "vector database",
        "faiss", "pinecone", "weaviate", "qdrant", "milvus",
        "elasticsearch", "opensearch", "bm25", "hybrid search", "rag"
    ],
    "ranking_systems": [
        "ranking", "recommendation", "recommender", "learning to rank",
        "ranker", "matching", "search relevance", "candidate matching"
    ],
    "evaluation_frameworks": [
        "ndcg", "mrr", "map", "precision", "recall", "offline benchmark",
        "a/b testing", "ab testing", "evaluation", "feedback loop",
        "quality regression", "metrics"
    ],
    "production_ml": [
        "production", "deployed", "real users", "monitoring", "pipeline",
        "scale", "latency", "on-call", "model serving", "feature pipeline",
        "schema drift", "index refresh", "data quality"
    ],
    "python_engineering": [
        "python", "backend", "api", "fastapi", "flask", "django",
        "sql", "spark", "airflow", "kafka", "docker", "kubernetes",
        "aws", "gcp", "azure", "microservice"
    ],
    "llm_depth": [
        "llm", "fine-tuning", "lora", "qlora", "peft", "transformers",
        "nlp", "rag", "prompt", "bge", "e5", "sentence-transformers"
    ],
    "product_shipper": [
        "built", "implemented", "shipped", "launched", "owned",
        "improved", "reduced", "increased", "users", "customer",
        "product", "worked closely"
    ],
    "leadership_mentoring": [
        "mentor", "mentored", "led", "lead", "staff", "senior",
        "principal", "managed", "team", "hiring", "reviewed"
    ],
    "startup_fit": [
        "startup", "founding", "scrappy", "ambiguity", "fast iteration",
        "ownership", "0 to 1", "early-stage", "series a"
    ],
    "evidence_strength": [
        "implemented", "designed", "built", "maintained", "owned",
        "deployed", "processed", "real-time", "daily", "on-call",
        "improved", "reduced", "increased", "led", "shipped"
    ],
}


IDEAL_VECTOR = {
    "retrieval_systems": 1.00,
    "ranking_systems": 1.00,
    "evaluation_frameworks": 0.95,
    "production_ml": 0.95,
    "python_engineering": 0.90,
    "llm_depth": 0.75,
    "product_shipper": 0.85,
    "leadership_mentoring": 0.60,
    "startup_fit": 0.70,
    "evidence_strength": 0.95,
}


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def normalize(text):
    return str(text or "").lower()


def count_matches(text, terms):
    text = normalize(text)
    score = 0.0

    for term in terms:
        term = normalize(term)
        if term in text:
            score += 1.0

        words = [w for w in term.replace("-", " ").replace("/", " ").split() if len(w) >= 4]
        for word in words:
            if word in text:
                score += 0.25

    return score


def skill_bonus(candidate, terms):
    skills = candidate.get("skills", [])
    bonus = 0.0

    for skill in skills:
        name = normalize(skill.get("name"))
        proficiency = normalize(skill.get("proficiency"))
        duration = int(skill.get("duration_months", 0) or 0)
        endorsements = int(skill.get("endorsements", 0) or 0)

        matched = any(normalize(term) in name or name in normalize(term) for term in terms)
        if not matched:
            continue

        if proficiency == "expert":
            bonus += 0.18
        elif proficiency == "advanced":
            bonus += 0.14
        elif proficiency == "intermediate":
            bonus += 0.09
        else:
            bonus += 0.05

        if duration >= 36:
            bonus += 0.06
        elif duration >= 18:
            bonus += 0.04
        elif duration >= 6:
            bonus += 0.02

        if endorsements >= 30:
            bonus += 0.05
        elif endorsements >= 10:
            bonus += 0.03

    return bonus


def dimension_source_text(candidate, dimension):
    texts = build_candidate_text(candidate)

    if dimension in {"retrieval_systems", "ranking_systems", "evaluation_frameworks", "production_ml"}:
        return texts["career_text"] + "\n" + texts["skills_text"]

    if dimension in {"product_shipper", "leadership_mentoring", "startup_fit", "evidence_strength"}:
        return texts["profile_text"] + "\n" + texts["career_text"]

    return texts["full_text"]


def build_candidate_vector(candidate):
    vector = {}

    graph_boosts, evidence_nodes = graph_dimension_boost(candidate)

    for dimension in DIMENSIONS:
        terms = DIMENSION_TERMS[dimension]
        source_text = dimension_source_text(candidate, dimension)

        raw_match = count_matches(source_text, terms)
        denominator = max(4, min(len(terms), 14))
        text_score = raw_match / denominator

        bonus = skill_bonus(candidate, terms)
        graph_boost = graph_boosts.get(dimension, 0.0)

        vector[dimension] = round(clamp(text_score + bonus + graph_boost), 4)

    return vector


def alignment_score(candidate_vector):
    weighted_sum = 0.0
    weight_total = 0.0

    for dimension, ideal_weight in IDEAL_VECTOR.items():
        weighted_sum += candidate_vector.get(dimension, 0.0) * ideal_weight
        weight_total += ideal_weight

    if weight_total == 0:
        return 0.0

    return round((weighted_sum / weight_total) * 100, 6)


def representation_confidence(candidate, candidate_vector):
    signals = candidate.get("redrob_signals", {})
    profile = candidate.get("profile", {})

    non_zero_dims = sum(1 for v in candidate_vector.values() if v >= 0.25)
    coverage = non_zero_dims / len(candidate_vector)

    profile_completeness = float(signals.get("profile_completeness_score", 50) or 50) / 100
    years = float(profile.get("years_of_experience", 0) or 0)

    seniority_fit = 1.0 if 5 <= years <= 9 else 0.75 if 4 <= years <= 11 else 0.5

    evidence_nodes = extract_evidence_graph(candidate)
    evidence_coverage = min(1.0, len(evidence_nodes) / 5)

    confidence = (
        0.35 * coverage +
        0.25 * profile_completeness +
        0.20 * seniority_fit +
        0.20 * evidence_coverage
    )

    return round(clamp(confidence), 4)


def compute_v3_scores(candidate):
    vector = build_candidate_vector(candidate)
    base_score = alignment_score(vector)
    confidence = representation_confidence(candidate, vector)
    evidence_nodes = extract_evidence_graph(candidate)

    confidence_adjusted_score = base_score * (0.80 + 0.20 * confidence)

    return {
        "candidate_vector": vector,
        "base_score": round(confidence_adjusted_score, 6),
        "confidence": confidence,
        "evidence_nodes": evidence_nodes,
    }