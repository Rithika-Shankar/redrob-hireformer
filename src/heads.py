from src.text_builder import build_candidate_text


def clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))


def text_contains_any(text, terms):
    text = text.lower()
    return any(term.lower() in text for term in terms)


def count_matches(text, terms):
    text = text.lower()
    return sum(1 for term in terms if term.lower() in text)


def get_skill_names(candidate):
    return [s.get("name", "").lower() for s in candidate.get("skills", [])]


def skill_quality_score(candidate, important_terms):
    skills = candidate.get("skills", [])
    score = 0

    for skill in skills:
        name = skill.get("name", "").lower()
        proficiency = skill.get("proficiency", "")
        duration = int(skill.get("duration_months", 0) or 0)
        endorsements = int(skill.get("endorsements", 0) or 0)

        if any(term.lower() in name for term in important_terms):
            if proficiency == "expert":
                score += 14
            elif proficiency == "advanced":
                score += 11
            elif proficiency == "intermediate":
                score += 7
            else:
                score += 4

            if duration >= 36:
                score += 5
            elif duration >= 18:
                score += 3

            if endorsements >= 30:
                score += 4
            elif endorsements >= 10:
                score += 2

    return clamp(score)


def score_retrieval_ranking_head(candidate):
    texts = build_candidate_text(candidate)
    text = texts["full_text"].lower()

    terms = [
        "embedding", "embeddings", "retrieval", "ranking", "recommendation",
        "recommender", "search", "semantic search", "vector", "vector database",
        "faiss", "pinecone", "weaviate", "qdrant", "milvus", "elasticsearch",
        "opensearch", "bm25", "hybrid search", "candidate matching"
    ]

    matched = count_matches(text, terms)
    score = matched * 8

    score += skill_quality_score(candidate, [
        "embedding", "retrieval", "ranking", "search", "milvus",
        "faiss", "pinecone", "elasticsearch", "opensearch"
    ])

    return clamp(score)


def score_production_ml_head(candidate):
    texts = build_candidate_text(candidate)
    text = texts["full_text"].lower()

    production_terms = [
        "production", "deployed", "deployment", "real users", "monitoring",
        "pipeline", "on-call", "latency", "scale", "scalable", "reliability",
        "data quality", "schema drift", "streaming", "kafka", "airflow",
        "spark", "feature pipeline", "model serving"
    ]

    ml_terms = [
        "machine learning", "ml", "model", "models", "feature engineering",
        "fine-tuning", "lora", "nlp", "llm", "classification", "prediction"
    ]

    score = count_matches(text, production_terms) * 6
    score += count_matches(text, ml_terms) * 4

    return clamp(score)


def score_python_engineering_head(candidate):
    texts = build_candidate_text(candidate)
    text = texts["full_text"].lower()

    terms = [
        "python", "api", "backend", "flask", "django", "fastapi",
        "sql", "spark", "airflow", "kafka", "docker", "kubernetes",
        "aws", "gcp", "azure", "microservice", "distributed"
    ]

    score = count_matches(text, terms) * 6
    score += skill_quality_score(candidate, [
        "python", "backend", "flask", "django", "fastapi",
        "sql", "spark", "airflow", "kafka"
    ])

    return clamp(score)


def score_evaluation_head(candidate):
    texts = build_candidate_text(candidate)
    text = texts["full_text"].lower()

    terms = [
        "ndcg", "mrr", "map", "ranking evaluation", "offline benchmark",
        "benchmark", "a/b testing", "ab testing", "experiment",
        "metrics", "evaluation", "feedback loop", "quality regression",
        "regression", "precision", "recall"
    ]

    score = count_matches(text, terms) * 12
    return clamp(score)


def score_product_shipper_head(candidate):
    texts = build_candidate_text(candidate)
    text = texts["full_text"].lower()

    terms = [
        "owned", "shipped", "built", "implemented", "launched",
        "worked closely", "product", "users", "customer", "recruiter",
        "startup", "founding", "mentor", "led", "improved", "reduced",
        "increased"
    ]

    score = count_matches(text, terms) * 5

    years = float(candidate.get("profile", {}).get("years_of_experience", 0) or 0)
    if 5 <= years <= 9:
        score += 15
    elif 4 <= years < 5 or 9 < years <= 11:
        score += 8

    return clamp(score)


def score_evidence_strength_head(candidate):
    texts = build_candidate_text(candidate)
    text = texts["full_text"].lower()
    signals = candidate.get("redrob_signals", {})

    score = 0

    # Strong evidence usually appears in career descriptions, not just skills.
    evidence_terms = [
        "implemented", "designed", "built", "maintained", "owned",
        "deployed", "processed", "real-time", "scale", "daily",
        "on-call", "improved", "reduced", "increased", "led"
    ]

    score += count_matches(text, evidence_terms) * 5

    assessment_scores = signals.get("skill_assessment_scores", {})
    if assessment_scores:
        avg_assessment = sum(assessment_scores.values()) / len(assessment_scores)
        score += avg_assessment * 0.25

    github = signals.get("github_activity_score", -1)
    if github and github > 0:
        score += min(15, github * 0.15)

    endorsements = signals.get("endorsements_received", 0)
    score += min(10, endorsements * 0.15)

    return clamp(score)


def compute_head_scores(candidate):
    return {
        "retrieval_ranking": score_retrieval_ranking_head(candidate),
        "production_ml": score_production_ml_head(candidate),
        "python_engineering": score_python_engineering_head(candidate),
        "evaluation": score_evaluation_head(candidate),
        "product_shipper": score_product_shipper_head(candidate),
        "evidence_strength": score_evidence_strength_head(candidate),
    }


def compute_base_score(head_scores):
    return (
        0.25 * head_scores["retrieval_ranking"] +
        0.20 * head_scores["production_ml"] +
        0.15 * head_scores["python_engineering"] +
        0.15 * head_scores["evaluation"] +
        0.10 * head_scores["product_shipper"] +
        0.15 * head_scores["evidence_strength"]
    )