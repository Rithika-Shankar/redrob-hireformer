CONSULTING_COMPANIES = {
    "tcs",
    "infosys",
    "wipro",
    "accenture",
    "cognizant",
    "capgemini",
    "mindtree",
}

RESEARCH_TERMS = {
    "research scientist",
    "research intern",
    "academic research",
    "publication",
    "phd researcher",
    "lab",
}

LANGCHAIN_ONLY_TERMS = {
    "langchain",
    "openai api",
    "chatgpt",
    "prompt engineering",
}

PRODUCTION_TERMS = {
    "production",
    "deployed",
    "deployment",
    "served",
    "real users",
    "pipeline",
    "monitoring",
    "on-call",
    "a/b testing",
    "ab testing",
    "scale",
    "latency",
    "reliability",
    "index refresh",
    "regression",
}

TITLE_CHASING_TERMS = {
    "principal",
    "staff",
    "director",
    "head of",
    "vp",
}


def lower_text(candidate):
    profile = candidate.get("profile", {})
    history = candidate.get("career_history", [])
    skills = candidate.get("skills", [])

    parts = [
        profile.get("headline", ""),
        profile.get("summary", ""),
        profile.get("current_title", ""),
        profile.get("current_company", ""),
        profile.get("current_industry", ""),
        profile.get("country", ""),
        profile.get("location", ""),
    ]

    for role in history:
        parts.extend([
            role.get("company", ""),
            role.get("title", ""),
            role.get("industry", ""),
            role.get("description", ""),
        ])

    for skill in skills:
        parts.append(skill.get("name", ""))

    return " ".join(parts).lower()


def has_any(text, terms):
    return any(term in text for term in terms)


def current_company(candidate):
    return candidate.get("profile", {}).get("current_company", "").lower()


def years_experience(candidate):
    return float(candidate.get("profile", {}).get("years_of_experience", 0) or 0)


def compute_risk_multiplier(candidate):
    text = lower_text(candidate)
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    multiplier = 1.0
    flags = []

    years = years_experience(candidate)
    engineering_terms = [
    "engineer", "developer", "ml", "machine learning", "data scientist",
    "ai", "backend", "software", "ranking", "recommendation", "search",
    "nlp", "platform", "applied scientist"
    ]

    non_engineering_titles = [
        "project manager", "business analyst", "operations manager",
        "marketing manager", "accountant", "customer support",
        "hr manager", "sales"
    ]

    current_title = profile.get("current_title", "").lower()

    if any(t in current_title for t in non_engineering_titles) and not has_any(text, engineering_terms):
        multiplier *= 0.35
        flags.append("current role is not engineering/AI-focused")
    if years < 4:
        multiplier *= 0.55
        flags.append("below expected seniority range")
    elif years < 5:
        multiplier *= 0.75
        flags.append("slightly below preferred experience range")
    elif years > 12:
        multiplier *= 0.80
        flags.append("well above intended 5-9 year band")

    country = profile.get("country", "").lower()
    willing_to_relocate = signals.get("willing_to_relocate", False)

    if country != "india" and not willing_to_relocate:
        multiplier *= 0.50
        flags.append("outside India and not relocation-ready")

    if has_any(text, RESEARCH_TERMS) and not has_any(text, PRODUCTION_TERMS):
        multiplier *= 0.55
        flags.append("research-heavy profile without production evidence")

    if has_any(text, LANGCHAIN_ONLY_TERMS) and not has_any(text, PRODUCTION_TERMS):
        multiplier *= 0.60
        flags.append("AI exposure appears wrapper/tool-based without production ML evidence")

    companies = [
        role.get("company", "").lower()
        for role in candidate.get("career_history", [])
    ]

    if companies:
        consulting_count = sum(1 for c in companies if c in CONSULTING_COMPANIES)
        if consulting_count == len(companies) and not has_any(text, PRODUCTION_TERMS):
            multiplier *= 0.65
            flags.append("consulting-heavy background with limited product/production evidence")

    titles = [
        role.get("title", "").lower()
        for role in candidate.get("career_history", [])
    ]

    short_roles = [
        role for role in candidate.get("career_history", [])
        if int(role.get("duration_months", 0) or 0) < 18
    ]

    if len(short_roles) >= 3 and has_any(" ".join(titles), TITLE_CHASING_TERMS):
        multiplier *= 0.70
        flags.append("possible title-chasing or frequent short-tenure pattern")

    github_score = signals.get("github_activity_score", -1)
    if github_score == -1 and "python" not in text:
        multiplier *= 0.85
        flags.append("weak public coding signal")

    return max(0.10, min(1.0, multiplier)), flags