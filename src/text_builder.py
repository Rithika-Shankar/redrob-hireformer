def safe_get(data, key, default=""):
    value = data.get(key, default)
    return "" if value is None else value


def build_skills_text(candidate):
    skills = candidate.get("skills", [])
    parts = []

    for skill in skills:
        name = safe_get(skill, "name")
        proficiency = safe_get(skill, "proficiency")
        duration = safe_get(skill, "duration_months", 0)
        endorsements = safe_get(skill, "endorsements", 0)

        parts.append(
            f"{name} ({proficiency}, {duration} months, {endorsements} endorsements)"
        )

    return "; ".join(parts)


def build_career_text(candidate):
    history = candidate.get("career_history", [])
    parts = []

    for role in history:
        title = safe_get(role, "title")
        company = safe_get(role, "company")
        industry = safe_get(role, "industry")
        duration = safe_get(role, "duration_months", 0)
        description = safe_get(role, "description")

        parts.append(
            f"{title} at {company} in {industry} for {duration} months. {description}"
        )

    return "\n".join(parts)


def build_education_text(candidate):
    education = candidate.get("education", [])
    parts = []

    for edu in education:
        degree = safe_get(edu, "degree")
        field = safe_get(edu, "field_of_study")
        institution = safe_get(edu, "institution")
        tier = safe_get(edu, "tier")

        parts.append(f"{degree} in {field} from {institution} ({tier})")

    return "; ".join(parts)


def build_candidate_text(candidate):
    profile = candidate.get("profile", {})

    profile_text = " ".join([
        safe_get(profile, "headline"),
        safe_get(profile, "summary"),
        safe_get(profile, "current_title"),
        safe_get(profile, "current_company"),
        safe_get(profile, "current_industry"),
        safe_get(profile, "location"),
        safe_get(profile, "country"),
        f"{safe_get(profile, 'years_of_experience', 0)} years experience",
    ])

    career_text = build_career_text(candidate)
    skills_text = build_skills_text(candidate)
    education_text = build_education_text(candidate)

    full_text = "\n".join([
        profile_text,
        career_text,
        skills_text,
        education_text,
    ])

    return {
        "profile_text": profile_text,
        "career_text": career_text,
        "skills_text": skills_text,
        "education_text": education_text,
        "full_text": full_text,
    }