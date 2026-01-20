import json
from pathlib import Path

import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, State, dcc, html

from nlp import analyze_resume

ROOT = Path(__file__).parent
ROLE_PACKS_PATH = ROOT / "role_packs.json"

with ROLE_PACKS_PATH.open("r", encoding="utf-8") as f:
    ROLE_PACKS = json.load(f)

ROLES = ROLE_PACKS.get("roles", {})
ROLE_OPTIONS = [{"label": ROLES[role]["display_name"], "value": role} for role in ROLES]

COACHING_CONTENT = {
    "data_scientist": {
        "projects": [
            "Build a customer churn model with model interpretability (SHAP) and a simple dashboard.",
            "Create an end-to-end A/B test analysis with clear business recommendations.",
        ],
        "bullets": [
            "Built a $X%$ improvement classifier using $Y$ features; validated with cross-validation and ROC-AUC.",
            "Designed an experiment and analyzed results to improve conversion by $X%$.",
            "Deployed a reproducible ML pipeline using Python, scikit-learn, and automated reporting.",
        ],
    },
    "data_engineer": {
        "projects": [
            "Create a batch ETL pipeline that ingests APIs, transforms data, and loads into a warehouse.",
            "Build a streaming pipeline using Kafka-like patterns and store results for analytics.",
        ],
        "bullets": [
            "Designed and built ETL pipelines handling $X$ records/day with $Y%$ SLA reliability.",
            "Optimized SQL and data models to reduce query times by $X%$.",
            "Automated data validation and monitoring to improve data quality and alerting.",
        ],
    },
}

ROLE_SUGGESTIONS = {
    "data_scientist": [
        "Highlight modeling methods (regression/classification), validation metrics, and impact.",
        "Add tools like Python, pandas, scikit-learn, and visualization libraries explicitly.",
        "Show end-to-end ML workflow: data cleaning → features → model → evaluation.",
    ],
    "data_engineer": [
        "Emphasize data pipeline work (ETL, orchestration, monitoring) with scale/volume.",
        "Call out cloud services (S3/EC2/Lambda) and SQL optimization experience.",
        "Include reliability and automation details (scheduling, data quality checks).",
    ],
}

app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css",
    ],
)
app.title = "ATS-Style Resume Scanner"

SAMPLE_RESUMES = {
    "data_scientist": [
        {
            "label": "Sample DS Resume",
            "value": "ds_001",
            "text": "Data Scientist with 3+ years of experience in Python and pandas. Built machine learning models with scikit-learn for churn prediction and used SQL for data extraction. Strong background in statistics, feature engineering, and data visualization (matplotlib, seaborn). Designed A/B tests and communicated results to stakeholders.",
        }
    ],
    "data_engineer": [
        {
            "label": "Sample DE Resume",
            "value": "de_001",
            "text": "Data Engineer with experience in building ETL pipelines using Python and SQL. Designed data models for analytics and implemented data quality checks. Built workflows with Airflow and deployed pipelines on AWS (S3, EC2). Focused on reliable data pipelines and monitoring.",
        }
    ],
}

app.layout = html.Div(
    children=[
        dbc.Navbar(
            className="app-navbar vs-navbar",
            children=[
                dbc.Container(
                    fluid=True,
                    className="d-flex align-items-center",
                    children=[
                        html.Div(
                            className="d-flex align-items-center gap-2",
                            children=[
                                html.Img(src="/assets/logo.svg", className="app-logo"),
                                html.Span("VolScan", className="navbar-brand fw-bold"),
                            ],
                        ),
                                html.Div("New Scan", className="navbar-title mx-auto"),
                        html.Div(
                            className="d-flex align-items-center gap-3",
                            children=[
                                html.Span("Explainable matching + coaching", className="navbar-tagline"),
                                html.Div(className="user-avatar", children="UT"),
                            ],
                        ),
                    ],
                )
            ],
        ),
        dbc.Container(
            fluid=False,
            className="py-4",
            children=[
                dbc.Row(
                    className="g-4",
                    children=[
                        dbc.Col(
                            md=3,
                            children=[
                                html.Div(
                                    className="sidebar vs-sidebar",
                                    children=[
                                        html.Div("Navigation", className="sidebar-title"),
                                        dbc.Nav(
                                            className="vs-nav",
                                            vertical=True,
                                            pills=True,
                                            children=[
                                                dbc.NavLink(
                                                    [html.I(className="bi bi-stars me-2"), "New Scan"],
                                                    active=True,
                                                    href="#",
                                                ),
                                                dbc.NavLink(
                                                    [html.I(className="bi bi-clock-history me-2"), "Scan History"],
                                                    disabled=True,
                                                    href="#",
                                                ),
                                                dbc.NavLink(
                                                    [html.I(className="bi bi-compass me-2"), "Coaching Paths"],
                                                    disabled=True,
                                                    href="#",
                                                ),
                                                dbc.NavLink(
                                                    [html.I(className="bi bi-gear me-2"), "Settings"],
                                                    disabled=True,
                                                    href="#",
                                                ),
                                            ],
                                        ),
                                        html.Hr(),
                                        html.Div(
                                            className="muted small",
                                            children="Tip: Use a sample JD to demo quickly.",
                                        ),
                                        html.Hr(),
                                        dbc.Card(
                                            className="card-surface",
                                            children=[
                                                dbc.CardHeader("Actionable Suggestions"),
                                                dbc.CardBody(
                                                    html.Div(
                                                        id="suggestions",
                                                        children="Suggestions will appear after a scan.",
                                                    )
                                                ),
                                            ],
                                        ),
                                        html.Hr(),
                                        dbc.Card(
                                            className="card-surface",
                                            children=[
                                                dbc.CardHeader("Overlap Terms"),
                                                dbc.CardBody(
                                                    html.Div(
                                                        id="overlap-terms",
                                                        children="No terms yet.",
                                                    )
                                                ),
                                            ],
                                        ),
                                        html.Hr(),
                                        dbc.Card(
                                            className="card-surface",
                                            children=[
                                                dbc.CardHeader("Missing Terms"),
                                                dbc.CardBody(
                                                    html.Div(
                                                        id="missing-terms",
                                                        children="No terms yet.",
                                                    )
                                                ),
                                            ],
                                        ),
                                        html.Hr(),
                                        dbc.Card(
                                            className="card-surface",
                                            children=[
                                                dbc.CardHeader("Role Coverage Checklist"),
                                                dbc.CardBody(
                                                    children=[
                                                        html.Div(id="coverage-checklist"),
                                                        html.Div(
                                                            className="muted mt-2",
                                                            children="Preview: Python, SQL, ETL, Cloud, Data Modeling",
                                                        ),
                                                    ]
                                                ),
                                            ],
                                        ),
                                    ],
                                )
                            ],
                        ),
                        dbc.Col(
                            md=9,
                            children=[
                                html.Div(
                                    className="page-header",
                                    children=[
                                        html.H1("New scan", className="vs-page-title"),
                                        html.P(
                                            "Paste resume + job description to generate an explainable match and coaching plan.",
                                            className="vs-page-subtitle",
                                        ),
                                    ],
                                ),
                                dbc.Row(
                                    className="g-4",
                                    children=[
                                        dbc.Col(
                                            md=6,
                                            children=[
                                                dbc.Card(
                                                    className="card-surface step-card",
                                                    children=[
                                                        dbc.CardHeader("Step 1: Resume"),
                                                        dbc.CardBody(
                                                            children=[
                                                                html.P(
                                                                    "Paste plain text. Avoid images, headers, and tables for best results.",
                                                                    className="muted",
                                                                ),
                                                                dbc.Label("Role"),
                                                                dcc.Dropdown(
                                                                    id="role",
                                                                    options=ROLE_OPTIONS,
                                                                    value="data_scientist",
                                                                    clearable=False,
                                                                ),
                                                                dbc.Label("Load sample resume", className="mt-2"),
                                                                dcc.Dropdown(
                                                                    id="sample-resume",
                                                                    options=[],
                                                                    placeholder="Select a sample resume",
                                                                ),
                                                                dcc.Textarea(
                                                                    id="resume-text",
                                                                    className="w-100 mt-3",
                                                                    placeholder="Paste resume text here...",
                                                                    style={"height": "260px"},
                                                                ),
                                                            ]
                                                        ),
                                                    ],
                                                )
                                            ],
                                        ),
                                        dbc.Col(
                                            md=6,
                                            children=[
                                                dbc.Card(
                                                    className="card-surface step-card",
                                                    children=[
                                                        dbc.CardHeader("Step 2: Job description"),
                                                        dbc.CardBody(
                                                            children=[
                                                                html.P(
                                                                    "Exclude legal disclaimers and benefits for a cleaner match.",
                                                                    className="muted",
                                                                ),
                                                                dbc.Label("Load sample JD"),
                                                                dcc.Dropdown(
                                                                    id="sample-jd",
                                                                    options=[],
                                                                    placeholder="Select a sample JD",
                                                                ),
                                                                dcc.Textarea(
                                                                    id="jd-text",
                                                                    className="w-100 mt-3",
                                                                    placeholder="Paste job description text here...",
                                                                    style={"height": "260px"},
                                                                ),
                                                            ]
                                                        ),
                                                    ],
                                                )
                                            ],
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="vs-action-row",
                                    children=[
                                        html.Span(id="scan-status", className="vs-status-pill"),
                                        dbc.Button(
                                            "View Coaching Plan",
                                            id="view-coaching",
                                            color="secondary",
                                        ),
                                        dbc.Button(
                                            "Run ATS Scan",
                                            id="run-scan",
                                            n_clicks=0,
                                            color="primary",
                                        ),
                                    ],
                                ),
                                html.Div(id="scan-message", className="mt-3"),
                                dbc.Row(
                                    className="g-4 mt-3",
                                    children=[
                                        dbc.Col(
                                            md=12,
                                            children=[
                                                dbc.Card(
                                                    id="results-card",
                                                    className="card-surface",
                                                    children=[
                                                        dbc.CardHeader("Results Summary"),
                                                        dbc.CardBody(
                                                            children=[
                                                                dbc.Spinner(
                                                                    color="primary",
                                                                    children=[
                                                                        html.Div(
                                                                            className="vs-score-shell",
                                                                            children=[
                                                                                html.Div("Match Score", className="muted"),
                                                                                html.Div(id="match-score", className="score-number", children="—"),
                                                                                dbc.Progress(id="match-progress", value=0, className="mt-2"),
                                                                            ],
                                                                        ),
                                                                        html.Div(
                                                                            className="metric-row mt-3",
                                                                            children=[
                                                                                html.Div(
                                                                                    className="vs-chip",
                                                                                    children=[html.Span("Keyword Similarity"), html.Strong(id="similarity-score", children="—")],
                                                                                ),
                                                                                html.Div(
                                                                                    className="vs-chip",
                                                                                    children=[html.Span("Role Coverage"), html.Strong(id="coverage-score", children="—")],
                                                                                ),
                                                                            ],
                                                                        ),
                                                                        html.Div(
                                                                            className="vs-empty mt-3",
                                                                            children=[
                                                                                html.I(className="bi bi-lightning-charge"),
                                                                                html.Div(
                                                                                    [
                                                                                        html.P("Run a scan to see results", className="mb-1"),
                                                                                        html.Ul(
                                                                                            [
                                                                                                html.Li("Match score and progress bar"),
                                                                                                html.Li("Keyword similarity + coverage"),
                                                                                                html.Li("Shows overlapping terms + missing JD terms"),
                                                                                            ]
                                                                                        ),
                                                                                    ]
                                                                                ),
                                                                            ],
                                                                        ),
                                                                        html.Div(
                                                                            className="muted small mt-2",
                                                                            children="Method: TF-IDF + cosine similarity + role coverage (explainable).",
                                                                        ),
                                                                    ],
                                                                )
                                                            ]
                                                        ),
                                                    ],
                                                )
                                            ],
                                        )
                                    ],
                                ),
                            ],
                        ),
                    ],
                )
            ],
        ),
    ]
)


def _list_block(title: str, items: list) -> html.Div:
    if not items:
        return html.Div([html.Div(className="text-muted", children="None yet")])
    return html.Div([html.Ul([html.Li(i) for i in items])])


def _badge_block(items: list, color: str = "secondary") -> html.Div:
    if not items:
        return html.Div(className="text-muted", children="No terms yet. Run a scan.")
    return html.Div(
        [
            html.Span(
                item,
                className=f"vs-pill {'missing' if color == 'warning' else 'overlap'}",
            )
            for item in items
        ]
    )


@app.callback(
    Output("scan-message", "children"),
    Output("match-score", "children"),
    Output("match-progress", "value"),
    Output("match-progress", "label"),
    Output("match-progress", "color"),
    Output("similarity-score", "children"),
    Output("coverage-score", "children"),
    Output("overlap-terms", "children"),
    Output("missing-terms", "children"),
    Output("coverage-checklist", "children"),
    Output("suggestions", "children"),
    Input("run-scan", "n_clicks"),
    State("role", "value"),
    State("resume-text", "value"),
    State("jd-text", "value"),
    prevent_initial_call=True,
)
def run_scan(n_clicks, role_key, resume_text, jd_text):
    def _safe_defaults(message: str, show_hint: bool) -> tuple:
        alert = dbc.Alert(message, color="info", className="mb-2") if message else ""
        overlap_block = _badge_block([], color="secondary")
        missing_block = _badge_block([], color="warning")
        coverage_block = html.Div(
            [
                html.Div([html.I(className="bi bi-check-circle me-2 text-success"), "Python"]),
                html.Div([html.I(className="bi bi-check-circle me-2 text-success"), "SQL"]),
                html.Div([html.I(className="bi bi-x-circle me-2 text-danger"), "ETL"]),
            ]
        )
        suggestion_block = _list_block("Actionable Suggestions", [])
        return (
            alert,
            "—",
            0,
            "0/100",
            "secondary",
            "—",
            "—",
            overlap_block,
            missing_block,
            coverage_block,
            suggestion_block,
        )

    resume_text = resume_text or ""
    jd_text = jd_text or ""

    if not resume_text.strip() or not jd_text.strip():
        return _safe_defaults("Paste resume + JD, then click Run ATS Scan.", show_hint=True)
    if len(resume_text.strip()) < 200 or len(jd_text.strip()) < 200:
        return _safe_defaults(
            "Please paste more complete resume and JD text (200+ characters each).",
            show_hint=True,
        )

    try:
        role_pack = ROLES[role_key]
        results = analyze_resume(resume_text, jd_text, role_pack)
    except Exception as exc:
        print(f"[Scan Error] {exc}")
        return _safe_defaults("Scan failed. Please check your inputs and try again.", show_hint=True)

    score_value = max(0, min(100, int(results["score"])))
    progress_color = "success" if score_value >= 70 else "warning" if score_value >= 45 else "danger"

    overlap_block = _badge_block(results["overlap_terms"], color="secondary")
    missing_block = _badge_block(results["missing_terms"], color="warning")

    present = results["present_skills"]
    missing_skills = results["missing_skills"]
    coverage_block = html.Div(
        [
            html.Div(
                [
                    html.I(className="bi bi-check-circle me-2 text-success"),
                    ", ".join(present) or "None",
                ]
            ),
            html.Div(
                [
                    html.I(className="bi bi-x-circle me-2 text-danger"),
                    ", ".join(missing_skills) or "None",
                ]
            ),
        ]
    )

    suggestions = results.get("suggestions", []) + ROLE_SUGGESTIONS.get(role_key, [])
    suggestion_block = _list_block("Actionable Suggestions", suggestions[:7])

    return (
        "",
        f"{score_value}",
        score_value,
        f"{score_value}/100",
        progress_color,
        f"{results['similarity']:.1f}",
        f"{results['coverage']:.1f}",
        overlap_block,
        missing_block,
        coverage_block,
        suggestion_block,
    )


@app.callback(
    Output("sample-jd", "options"),
    Output("sample-resume", "options"),
    Input("role", "value"),
)
def update_sample_options(role_key):
    role_pack = ROLES.get(role_key, {})
    jd_samples = role_pack.get("sample_jds", [])
    jd_options = [
        {
            "label": f"{s.get('title', 'Sample JD')} ({s.get('jd_id', '')})",
            "value": s.get("jd_id"),
        }
        for s in jd_samples
    ]
    resume_options = [
        {"label": s["label"], "value": s["value"]}
        for s in SAMPLE_RESUMES.get(role_key, [])
    ]
    return jd_options, resume_options


@app.callback(
    Output("jd-text", "value"),
    Input("sample-jd", "value"),
    State("role", "value"),
    prevent_initial_call=True,
)
def load_sample_jd(sample_id, role_key):
    if not sample_id:
        return ""
    role_pack = ROLES.get(role_key, {})
    for sample in role_pack.get("sample_jds", []):
        if sample.get("jd_id") == sample_id:
            return sample.get("text", "")
    return ""


@app.callback(
    Output("resume-text", "value"),
    Input("sample-resume", "value"),
    State("role", "value"),
    prevent_initial_call=True,
)
def load_sample_resume(sample_id, role_key):
    if not sample_id:
        return ""
    for sample in SAMPLE_RESUMES.get(role_key, []):
        if sample.get("value") == sample_id:
            return sample.get("text", "")
    return ""


@app.callback(
    Output("run-scan", "disabled"),
    Output("scan-status", "children"),
    Input("resume-text", "value"),
    Input("jd-text", "value"),
)
def update_scan_ready(resume_text, jd_text):
    resume_len = len((resume_text or "").strip())
    jd_len = len((jd_text or "").strip())
    ready = resume_len >= 200 and jd_len >= 200
    if ready:
        return False, dbc.Badge("Ready", color="success", className="status-pill vs-status-pill")
    return True, dbc.Badge(
        "Ready when both fields have 200+ chars",
        color="secondary",
        className="status-pill vs-status-pill",
    )


if __name__ == "__main__":
    app.run(debug=True)
