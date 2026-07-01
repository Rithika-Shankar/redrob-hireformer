import json
import heapq

from src.ranker import evaluate_candidate


STAGE1_TERMS = [
    "ai engineer", "machine learning engineer", "ml engineer",
    "nlp engineer", "search engineer", "recommendation systems",
    "recommender", "ranking", "learning to rank", "retrieval",
    "embeddings", "semantic search", "vector database", "faiss",
    "pinecone", "weaviate", "qdrant", "milvus", "bm25",
    "opensearch", "elasticsearch", "python", "llm", "rag",
    "fine-tuning", "lora", "qlora", "peft", "production",
    "deployed", "a/b testing", "ndcg", "mrr", "map"
]


BAD_TITLE_TERMS = [
    "accountant", "marketing manager", "sales", "hr manager",
    "customer support", "graphic designer", "civil engineer",
    "mechanical engineer", "operations manager"
]


def lower_candidate_text(candidate):
    profile = candidate.get("profile", {})
    parts = [
        profile.get("headline", ""),
        profile.get("summary", ""),
        profile.get("current_title", ""),
        profile.get("current_industry", ""),
        profile.get("country", ""),
        profile.get("location", ""),
    ]

    for role in candidate.get("career_history", []):
        parts.append(role.get("title", ""))
        parts.append(role.get("description", ""))
        parts.append(role.get("industry", ""))

    for skill in candidate.get("skills", []):
        parts.append(skill.get("name", ""))

    return " ".join(parts).lower()


def stage1_score(candidate):
    text = lower_candidate_text(candidate)
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    score = 0.0

    for term in STAGE1_TERMS:
        if term in text:
            score += 3.0

    title = profile.get("current_title", "").lower()

    if any(t in title for t in ["ai engineer", "machine learning", "ml engineer", "nlp engineer", "search engineer", "recommendation"]):
        score += 25

    if any(t in title for t in BAD_TITLE_TERMS):
        score -= 20

    years = float(profile.get("years_of_experience", 0) or 0)
    if 5 <= years <= 9:
        score += 20
    elif 4 <= years <= 11:
        score += 10
    else:
        score -= 10

    if signals.get("open_to_work_flag"):
        score += 5
    if signals.get("willing_to_relocate"):
        score += 5

    response_rate = signals.get("recruiter_response_rate")
    if response_rate is not None:
        score += float(response_rate) * 5

    return score


def select_stage1_candidates(candidates_path, shortlist_size=5000):
    heap = []

    with open(candidates_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            candidate = json.loads(line)
            score = stage1_score(candidate)
            item = (score, candidate["candidate_id"], candidate)

            if len(heap) < shortlist_size:
                heapq.heappush(heap, item)
            else:
                if item[0] > heap[0][0]:
                    heapq.heapreplace(heap, item)

    shortlist = [item[2] for item in heap]
    shortlist.sort(key=lambda c: (-stage1_score(c), c["candidate_id"]))

    return shortlist


def fast_rank_candidates_from_jsonl(candidates_path, blueprint, shortlist_size=5000):
    shortlist = select_stage1_candidates(candidates_path, shortlist_size=shortlist_size)

    results = []
    for candidate in shortlist:
        results.append(evaluate_candidate(candidate, blueprint))

    results.sort(key=lambda x: (-x["score"], x["candidate_id"]))

    for idx, result in enumerate(results, start=1):
        result["rank"] = idx

    return results