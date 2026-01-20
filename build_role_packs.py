import json
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from nlp import normalize_text

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_PATH = Path(__file__).parent / "role_packs.json"

JD_COL_KEYWORDS = ["job", "jd", "description", "posting", "responsibilities", "requirements"]
TITLE_COL_KEYWORDS = ["title", "role", "position", "category"]

ROLE_KEYWORDS = {
    "data_scientist": [
        "data scientist",
        "machine learning",
        "ml",
        "modeling",
        "statistics",
        "regression",
        "classification",
        "experiment",
        "ab test",
        "nlp",
    ],
    "data_engineer": [
        "data engineer",
        "etl",
        "pipeline",
        "airflow",
        "kafka",
        "spark",
        "warehouse",
        "orchestration",
    ],
}

ROLE_BASE = {
    "data_scientist": {
        "display_name": "Data Scientist",
        "must_have": [
            "Python",
            "pandas",
            "scikit-learn",
            "statistics",
            "machine learning",
            "SQL",
            "data visualization",
            "feature engineering",
            "experimentation",
            "model evaluation",
            "data cleaning",
            "communication",
        ],
        "nice_to_have": [
            "deep learning",
            "A/B testing",
            "NLP",
            "time series",
            "cloud",
            "Spark",
            "dashboarding",
        ],
        "aliases": {
            "scikit-learn": ["sklearn"],
            "machine learning": ["ml", "modeling"],
            "data visualization": ["matplotlib", "seaborn", "plotly"],
            "statistics": ["statistical analysis"],
            "python": ["python programming"],
            "sql": ["structured query language"],
            "ab testing": ["a/b testing", "experimentation"],
            "nlp": ["natural language processing"],
            "dashboarding": ["tableau", "power bi"],
        },
    },
    "data_engineer": {
        "display_name": "Data Engineer",
        "must_have": [
            "Python",
            "SQL",
            "ETL",
            "data pipelines",
            "data modeling",
            "cloud",
            "data quality",
            "orchestration",
            "data warehousing",
            "monitoring",
            "automation",
            "reliability",
        ],
        "nice_to_have": [
            "Spark",
            "Kafka",
            "Docker",
            "CI/CD",
            "streaming",
            "Airflow",
            "dbt",
        ],
        "aliases": {
            "etl": ["data pipeline", "pipelines"],
            "data pipelines": ["etl", "data pipeline"],
            "cloud": ["aws", "s3", "ec2", "lambda"],
            "orchestration": ["airflow", "scheduler"],
            "data quality": ["validation", "dq"],
            "sql": ["structured query language"],
            "k8s": ["kubernetes"],
            "ml": ["machine learning"],
        },
    },
}


def read_csv_safe(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.read_csv(path, encoding="latin-1", encoding_errors="ignore")


def profile_df(path: Path, df: pd.DataFrame) -> None:
    print(f"\n[Profile] {path.name}")
    print(f"Rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")


def text_column_stats(df: pd.DataFrame) -> Dict[str, float]:
    stats = {}
    for col in df.columns:
        if df[col].dtype == "object":
            series = df[col].dropna().astype(str)
            if not series.empty:
                stats[col] = series.str.len().mean()
    return stats


def score_jd_column(col_name: str, avg_len: float) -> float:
    col_lower = col_name.lower()
    name_hits = sum(1 for kw in JD_COL_KEYWORDS if kw in col_lower)
    length_score = avg_len / 200
    return name_hits * 2 + length_score


def find_best_text_column(df: pd.DataFrame) -> Tuple[str, float]:
    stats = text_column_stats(df)
    if not stats:
        return "", 0.0
    scored = {col: score_jd_column(col, avg_len) for col, avg_len in stats.items()}
    best_col = max(scored, key=scored.get)
    return best_col, scored[best_col]


def select_jd_file(dfs: Dict[Path, pd.DataFrame]) -> Path:
    scores = {}
    for path, df in dfs.items():
        best_col, best_score = find_best_text_column(df)
        scores[path] = (best_score, best_col)
    return max(scores.keys(), key=lambda p: scores[p][0])


def find_title_column(df: pd.DataFrame) -> str:
    for col in df.columns:
        col_lower = col.lower()
        if any(k in col_lower for k in TITLE_COL_KEYWORDS):
            return col
    return ""


def find_jd_column(df: pd.DataFrame) -> str:
    stats = text_column_stats(df)
    if not stats:
        return ""
    keyword_candidates = [
        col
        for col in df.columns
        if any(k in col.lower() for k in JD_COL_KEYWORDS)
    ]
    if keyword_candidates:
        return max(keyword_candidates, key=lambda c: stats.get(c, 0))
    return max(stats, key=stats.get)


def classify_role(title: str, text: str) -> str:
    combined = f"{title} {text}".lower()
    if "data engineer" in combined:
        return "data_engineer"
    if "data scientist" in combined:
        return "data_scientist"
    for role, keywords in ROLE_KEYWORDS.items():
        if any(k in combined for k in keywords):
            return role
    return ""


def is_near_duplicate(text: str, existing: List[str]) -> bool:
    for other in existing:
        if SequenceMatcher(None, text, other).ratio() > 0.9:
            return True
    return False


def build_samples(df: pd.DataFrame, jd_col: str, title_col: str, source: str) -> Dict[str, List[Dict]]:
    samples = {"data_scientist": [], "data_engineer": []}
    seen_norm = {"data_scientist": [], "data_engineer": []}

    for idx, row in df.iterrows():
        jd_text = str(row.get(jd_col, "")).strip()
        if not jd_text:
            continue
        title = str(row.get(title_col, "")).strip() if title_col else ""
        role = classify_role(title, jd_text)
        if not role:
            continue
        jd_norm = normalize_text(jd_text)
        if is_near_duplicate(jd_norm, seen_norm[role]):
            continue
        seen_norm[role].append(jd_norm)
        samples[role].append(
            {
                "jd_id": f"{role[:2]}_{len(samples[role]) + 1:03d}",
                "title": title or ROLE_BASE[role]["display_name"],
                "text": jd_text[:2000],
                "source": source,
                "row_index": int(idx),
            }
        )
        if len(samples[role]) >= 5:
            if all(len(samples[r]) >= 3 for r in samples):
                break

    return samples


def main() -> None:
    if not DATA_DIR.exists():
        raise FileNotFoundError("Expected ./data folder with two CSV files.")

    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if len(csv_files) != 2:
        raise ValueError("Expected exactly two CSV files in ./data.")

    dfs = {path: read_csv_safe(path) for path in csv_files}
    for path, df in dfs.items():
        profile_df(path, df)

    jd_file = select_jd_file(dfs)
    jd_df = dfs[jd_file]

    jd_col = find_jd_column(jd_df)
    title_col = find_title_column(jd_df)

    print(f"\n[Detected] JD file: {jd_file.name}")
    print(f"[Detected] JD text column: {jd_col or 'None'}")
    print(f"[Detected] Title column: {title_col or 'None'}")

    samples = build_samples(jd_df, jd_col, title_col, jd_file.name)

    role_packs = {
        "schema_version": 1,
        "roles": {
            "data_scientist": {
                **ROLE_BASE["data_scientist"],
                "sample_jds": samples["data_scientist"],
            },
            "data_engineer": {
                **ROLE_BASE["data_engineer"],
                "sample_jds": samples["data_engineer"],
            },
        },
    }

    OUTPUT_PATH.write_text(json.dumps(role_packs, indent=2), encoding="utf-8")
    print(f"\n[Saved] {OUTPUT_PATH.name}")


if __name__ == "__main__":
    main()
