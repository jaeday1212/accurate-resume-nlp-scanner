import re
from typing import Dict, List, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


_WHITESPACE_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^a-z0-9\s]")


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = _PUNCT_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


def build_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(ngram_range=(1, 2), min_df=1, stop_words="english")


def overlap_and_missing_terms(
    resume_text: str,
    jd_text: str,
    top_n: int = 15,
) -> Tuple[List[str], List[str]]:
    if not resume_text or not jd_text:
        return [], []

    vectorizer = build_vectorizer()
    tfidf = vectorizer.fit_transform([resume_text, jd_text])
    resume_vec = tfidf[0].toarray().ravel()
    jd_vec = tfidf[1].toarray().ravel()
    feature_names = vectorizer.get_feature_names_out()

    jd_ranked = np.argsort(jd_vec)[::-1]
    overlap = []
    missing = []

    for idx in jd_ranked:
        if jd_vec[idx] <= 0:
            break
        term = feature_names[idx]
        if resume_vec[idx] > 0 and len(overlap) < top_n:
            overlap.append(term)
        elif resume_vec[idx] == 0 and len(missing) < top_n:
            missing.append(term)
        if len(overlap) >= top_n and len(missing) >= top_n:
            break

    return overlap, missing


def compute_similarity(resume_text: str, jd_text: str) -> float:
    if not resume_text or not jd_text:
        return 0.0
    vectorizer = build_vectorizer()
    tfidf = vectorizer.fit_transform([resume_text, jd_text])
    sim = cosine_similarity(tfidf[0], tfidf[1])[0][0]
    return float(sim)


def skill_coverage(
    resume_text: str,
    must_have: List[str],
    aliases: Dict[str, List[str]],
) -> Tuple[int, int, List[str], List[str]]:
    resume_text = normalize_text(resume_text)
    present = []
    missing = []

    for skill in must_have:
        skill_key = normalize_text(skill)
        alias_list = [normalize_text(a) for a in aliases.get(skill_key, [])]
        terms = [skill_key] + alias_list
        found = any(term in resume_text for term in terms)
        if found:
            present.append(skill)
        else:
            missing.append(skill)

    return len(present), len(must_have), present, missing


def final_score(similarity: float, coverage: float) -> int:
    score = round(0.7 * similarity + 0.3 * coverage)
    return max(0, min(100, score))


def generate_suggestions(
    missing_skills: List[str],
    missing_terms: List[str],
    max_suggestions: int = 7,
) -> List[str]:
    suggestions = []
    if missing_skills:
        suggestions.append(
            f"Add evidence for: {', '.join(missing_skills[:4])}."
        )
    if missing_terms:
        suggestions.append(
            f"Incorporate keywords like: {', '.join(missing_terms[:6])}."
        )
    suggestions.append("Quantify impact with metrics (time saved, accuracy, cost reduction).")
    suggestions.append("Mirror role language from the JD in your bullet points.")
    suggestions.append("Lead bullets with action verbs and measurable outcomes.")
    return suggestions[:max_suggestions]


def analyze_resume(
    resume_text: str,
    jd_text: str,
    role_pack: Dict,
) -> Dict:
    resume_norm = normalize_text(resume_text)
    jd_norm = normalize_text(jd_text)

    similarity = compute_similarity(resume_norm, jd_norm) * 100
    overlap, missing_terms = overlap_and_missing_terms(resume_norm, jd_norm)

    must_have = role_pack.get("must_have", [])
    aliases = role_pack.get("aliases", {})
    present_count, total_count, present, missing_skills = skill_coverage(
        resume_norm, must_have, aliases
    )
    coverage = (present_count / total_count * 100) if total_count else 0.0
    score = final_score(similarity, coverage)

    suggestions = generate_suggestions(missing_skills, missing_terms)

    return {
        "similarity": similarity,
        "coverage": coverage,
        "score": score,
        "overlap_terms": overlap,
        "missing_terms": missing_terms,
        "present_skills": present,
        "missing_skills": missing_skills,
        "suggestions": suggestions,
    }
