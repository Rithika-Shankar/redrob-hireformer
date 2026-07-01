from dataclasses import dataclass, field


@dataclass
class HiringBlueprint:
    role: str
    company: str
    location: str
    experience_min: float
    experience_max: float

    core_mission: str
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    behavioral_traits: list[str] = field(default_factory=list)
    disqualifiers: list[str] = field(default_factory=list)
    hidden_expectations: list[str] = field(default_factory=list)


def build_hiring_blueprint(jd_text: str) -> HiringBlueprint:
    """
    Deterministic JD parser for this hackathon role.
    No API calls. No network. Safe for 5-minute CPU-only ranking.
    """

    return HiringBlueprint(
        role="Senior AI Engineer — Founding Team",
        company="Redrob AI",
        location="Pune/Noida, India; hybrid; open to relocation from Tier-1 Indian cities",
        experience_min=5.0,
        experience_max=9.0,

        core_mission=(
            "Own and improve candidate retrieval, ranking, matching, and evaluation systems "
            "for an AI-native talent intelligence platform."
        ),

        required_skills=[
            "Python",
            "embeddings",
            "retrieval systems",
            "ranking systems",
            "candidate matching",
            "vector databases",
            "hybrid search",
            "evaluation frameworks",
            "NDCG",
            "MRR",
            "MAP",
            "A/B testing",
            "production ML systems",
            "LLMs",
        ],

        preferred_skills=[
            "LLM fine-tuning",
            "LoRA",
            "QLoRA",
            "PEFT",
            "learning to rank",
            "XGBoost ranking",
            "neural ranking",
            "HR tech",
            "recruiting tech",
            "marketplace products",
            "distributed systems",
            "large-scale inference",
            "open-source AI/ML contributions",
        ],

        responsibilities=[
            "audit existing BM25 and rule-based ranking systems",
            "ship a v2 ranking system",
            "improve recruiter engagement metrics",
            "build embeddings and hybrid retrieval systems",
            "use LLM-based reranking where appropriate",
            "set up offline benchmarks",
            "set up online A/B testing",
            "create recruiter feedback loops",
            "mentor future AI engineering hires",
            "work with recruiter-experience product team",
        ],

        behavioral_traits=[
            "scrappy product engineering",
            "shipper mindset",
            "ownership",
            "comfort with ambiguity",
            "pragmatic ML thinking",
            "recruiter workflow empathy",
            "fast iteration",
            "technical depth",
            "product judgment",
            "mentoring ability",
        ],

        disqualifiers=[
            "pure research without production deployment",
            "AI experience only from recent LangChain or OpenAI wrapper projects",
            "no hands-on production coding in the last 18 months",
            "pure consulting-only career without product engineering depth",
            "title-chasing career pattern",
            "candidate not open to Pune/Noida hybrid or relocation",
            "keyword-stuffed profile with weak evidence",
        ],

        hidden_expectations=[
            "must balance ML depth with product shipping",
            "should understand retrieval and ranking before the LLM hype cycle",
            "should be able to build imperfect but useful systems quickly",
            "should care about evaluation and feedback loops",
            "should be comfortable joining a founding AI team",
        ],
    )


def blueprint_to_dict(bp: HiringBlueprint) -> dict:
    return {
        "role": bp.role,
        "company": bp.company,
        "location": bp.location,
        "experience_min": bp.experience_min,
        "experience_max": bp.experience_max,
        "core_mission": bp.core_mission,
        "required_skills": bp.required_skills,
        "preferred_skills": bp.preferred_skills,
        "responsibilities": bp.responsibilities,
        "behavioral_traits": bp.behavioral_traits,
        "disqualifiers": bp.disqualifiers,
        "hidden_expectations": bp.hidden_expectations,
    }