from src.text_builder import build_candidate_text


EVIDENCE_PATTERNS = [
    {
        "label": "vector retrieval evidence",
        "terms": ["faiss", "pinecone", "weaviate", "qdrant", "milvus", "vector database", "embeddings", "semantic search"],
        "supports": {
            "retrieval_systems": 1.00,
            "ranking_systems": 0.45,
            "production_ml": 0.45,
            "evidence_strength": 0.35,
        },
    },
    {
        "label": "ranking/recommendation evidence",
        "terms": ["ranking", "recommendation", "recommender", "learning to rank", "ranker", "search relevance", "matching"],
        "supports": {
            "ranking_systems": 1.00,
            "retrieval_systems": 0.55,
            "evaluation_frameworks": 0.40,
            "evidence_strength": 0.35,
        },
    },
    {
        "label": "evaluation evidence",
        "terms": ["ndcg", "mrr", "map", "a/b testing", "ab testing", "offline benchmark", "metrics", "evaluation"],
        "supports": {
            "evaluation_frameworks": 1.00,
            "ranking_systems": 0.55,
            "product_shipper": 0.30,
            "evidence_strength": 0.35,
        },
    },
    {
        "label": "production deployment evidence",
        "terms": ["production", "deployed", "real users", "monitoring", "latency", "scale", "on-call", "model serving"],
        "supports": {
            "production_ml": 1.00,
            "python_engineering": 0.45,
            "product_shipper": 0.45,
            "evidence_strength": 0.55,
        },
    },
    {
        "label": "data/feature pipeline evidence",
        "terms": ["airflow", "spark", "kafka", "feature pipeline", "data quality", "schema drift", "streaming", "etl"],
        "supports": {
            "production_ml": 0.75,
            "python_engineering": 0.60,
            "retrieval_systems": 0.25,
            "evidence_strength": 0.45,
        },
    },
    {
        "label": "LLM depth evidence",
        "terms": ["llm", "fine-tuning", "lora", "qlora", "peft", "rag", "transformers", "sentence-transformers"],
        "supports": {
            "llm_depth": 1.00,
            "retrieval_systems": 0.45,
            "production_ml": 0.30,
            "evidence_strength": 0.25,
        },
    },
    {
        "label": "product shipping evidence",
        "terms": ["shipped", "launched", "owned", "built", "implemented", "improved", "worked closely", "users", "customer"],
        "supports": {
            "product_shipper": 1.00,
            "startup_fit": 0.45,
            "evidence_strength": 0.60,
        },
    },
    {
        "label": "leadership/mentoring evidence",
        "terms": ["mentor", "mentored", "led", "lead", "managed", "team", "reviewed", "hiring"],
        "supports": {
            "leadership_mentoring": 1.00,
            "product_shipper": 0.35,
            "startup_fit": 0.25,
            "evidence_strength": 0.30,
        },
    },
]


def normalize(text):
    return str(text or "").lower()


def evidence_strength_from_text(text, terms):
    text = normalize(text)
    hits = 0

    for term in terms:
        term = normalize(term)
        if term in text:
            hits += 1

    if hits == 0:
        return 0.0

    return min(1.0, hits / max(2, len(terms) * 0.35))


def extract_evidence_graph(candidate):
    texts = build_candidate_text(candidate)
    full_text = texts["full_text"]
    career_text = texts["career_text"]
    skills_text = texts["skills_text"]

    evidence_nodes = []

    for pattern in EVIDENCE_PATTERNS:
        career_strength = evidence_strength_from_text(career_text, pattern["terms"])
        skill_strength = evidence_strength_from_text(skills_text, pattern["terms"])

        strength = max(career_strength, skill_strength * 0.75)

        if strength <= 0:
            continue

        evidence_nodes.append({
            "label": pattern["label"],
            "strength": round(strength, 4),
            "supports": pattern["supports"],
        })

    return evidence_nodes


def graph_dimension_boost(candidate):
    evidence_nodes = extract_evidence_graph(candidate)
    boosts = {}

    for node in evidence_nodes:
        node_strength = node["strength"]

        for dimension, support_weight in node["supports"].items():
            boosts[dimension] = boosts.get(dimension, 0.0) + node_strength * support_weight

    for dimension in boosts:
        boosts[dimension] = min(0.35, boosts[dimension] * 0.12)

    return boosts, evidence_nodes


def summarize_evidence_nodes(evidence_nodes, limit=3):
    ordered = sorted(evidence_nodes, key=lambda x: x["strength"], reverse=True)
    return [node["label"] for node in ordered[:limit]]