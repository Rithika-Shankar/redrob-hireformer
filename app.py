import json
import tempfile
import time
from typing import Any, Dict, List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.fast_ranker import fast_rank_candidates_from_jsonl
from src.loader import load_jsonl, load_docx_text, load_sample_json
from src.jd_parser import build_hiring_blueprint
from src.ranker import rank_candidates
from src.reasoning import generate_reasoning


st.set_page_config(
    page_title="HireFormer",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
:root {
    --bg:#f9fafb;
    --card:#ffffff;
    --text:#111827;
    --muted:#6b7280;
    --soft:#9ca3af;
    --line:#eef2f7;
    --indigo:#4f46e5;
    --indigo-soft:#eef2ff;
    --green:#10b981;
    --green-soft:#ecfdf5;
    --red:#e11d48;
    --red-soft:#fff1f2;
    --amber:#f59e0b;
}
[data-testid="stAppViewContainer"] { background: var(--bg); }
[data-testid="stHeader"] { background: transparent; height:0rem; }
[data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer { display:none !important; }
.block-container {
    max-width: 760px !important;
    padding-top: 0 !important;
    padding-left: 24px !important;
    padding-right: 24px !important;
    padding-bottom: 90px !important;
}
* { font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }

/* ---- top nav ---- */
.top-nav-wrap {
    width: 100vw;
    margin-left: calc(-50vw + 50%);
    background: rgba(255,255,255,.96);
    border-bottom: 1px solid #e5e7eb;
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(10px);
}
.top-nav-inner {
    max-width: 760px;
    margin: 0 auto;
    padding: 0 24px;
}
.top-nav-inner [data-testid="column"]:first-child { display:flex; align-items:center; }
.top-nav-inner [data-testid="column"]:last-child { display:flex; align-items:center; justify-content:flex-end; }
.brand { display:flex; align-items:center; gap:10px; color:var(--text); font-weight:850; font-size:18px; padding:14px 0; }
.brand-icon { width:32px; height:32px; border-radius:10px; background:var(--indigo); color:white; display:flex; align-items:center; justify-content:center; }
.top-nav-inner .stButton > button {
    background: var(--indigo-soft);
    color: var(--indigo);
    border: 1px solid #e0e7ff;
    font-weight: 800;
    font-size: 13px;
}
.top-nav-inner .stButton > button:hover {
    background: var(--indigo);
    color: white;
    border-color: var(--indigo);
}

.hero { text-align:center; padding:54px 0 22px; }
.hero-badge, .badge { display:inline-flex; align-items:center; gap:6px; background:var(--indigo-soft); color:var(--indigo); padding:7px 14px; border-radius:999px; font-size:11px; font-weight:850; letter-spacing:.08em; text-transform:uppercase; margin-bottom:12px; }
.hero-title { margin-top:14px; font-size:58px; line-height:1; font-weight:950; letter-spacing:-.055em; color:var(--text); }
.hero-title span { color:var(--indigo); }
.hero-sub { color:var(--muted); font-size:18px; margin-top:12px; }
.word-strip { margin-top:16px; color:var(--soft); display:flex; gap:12px; justify-content:center; font-size:14px; font-weight:650; }
.word-strip b { color:#374151; }
.card, .candidate-card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 22px;
    padding: 22px;
    box-shadow: 0 2px 12px rgba(15,23,42,.045);
    margin-bottom: 16px;
}
.plain-header { padding: 4px 2px 18px; }
.card-title { color:var(--soft); font-size:11px; font-weight:900; letter-spacing:.12em; text-transform:uppercase; margin-bottom:14px; }
.section-title { color:var(--soft); font-size:11px; font-weight:900; letter-spacing:.12em; text-transform:uppercase; margin:22px 2px 12px; }
.page-title { color:var(--text); font-size:30px; font-weight:950; letter-spacing:-.035em; margin-bottom:4px; }
.page-subtitle { color:var(--muted); font-size:15px; margin-bottom:24px; }
.chip { display:inline-block; padding:7px 13px; border-radius:999px; font-size:12px; font-weight:750; margin:4px 4px 4px 0; }
.green { background:var(--green-soft); color:#047857; border:1px solid #d1fae5; }
.indigo { background:var(--indigo-soft); color:var(--indigo); border:1px solid #e0e7ff; }
.red { background:var(--red-soft); color:var(--red); border:1px solid #ffe4e6; }
.gray { background:#f3f4f6; color:#4b5563; border:1px solid #e5e7eb; }
.upload-box { background:white; border:1px dashed #d1d5db; border-radius:18px; padding:0; margin-bottom:14px; }
.upload-box [data-testid="stFileUploader"] { padding: 12px 16px; }
.upload-box section { border:0 !important; padding: 0 !important; background: transparent !important; }
.upload-box label { font-weight:750 !important; color:var(--text) !important; }
.feature-row { display:flex; justify-content:center; gap:40px; margin-top:44px; border-top:1px solid var(--line); padding-top:22px; text-align:center; }
.feature { min-width: 130px; }
.feature-icon { font-size:26px; margin-bottom:4px; }
.feature-title { color:var(--text); font-weight:800; font-size:14px; }
.feature-desc { color:var(--muted); font-size:12px; margin-top:2px; }
.candidate-top { display:flex; align-items:flex-start; gap:15px; }
.rank-icon { width:40px; font-size:22px; text-align:center; white-space:nowrap; flex-shrink:0; line-height:1; }
.score-ring { width:60px; height:60px; border-radius:999px; background:conic-gradient(var(--green) var(--score), #f1f5f9 0); display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.score-inner { width:46px; height:46px; border-radius:999px; background:white; display:flex; align-items:center; justify-content:center; color:var(--text); font-size:13px; font-weight:900; }
.candidate-id { color:var(--text); font-size:16px; font-weight:900; }
.candidate-title { color:var(--muted); font-size:13px; }
.reason { color:var(--muted); font-size:13px; line-height:1.55; margin-top:10px; }
.panel-grid { display:grid; grid-template-columns: repeat(4,1fr); gap:10px; }
.panel-box { background:#f9fafb; border:1px solid #f3f4f6; border-radius:16px; padding:13px; text-align:center; }
.panel-role { font-size:11px; color:var(--muted); font-weight:850; text-transform:uppercase; }
.panel-score { font-size:24px; font-weight:950; color:var(--text); margin-top:3px; }

.candidate-card-compact { background: var(--card); border: 1px solid var(--line); border-radius: 18px; padding: 14px; box-shadow: 0 2px 10px rgba(15,23,42,.04); margin-bottom: 12px; }
.compact-top-row { display:flex; align-items:center; justify-content:space-between; gap:8px; }
.compact-rank { font-size:13px; color:var(--soft); font-weight:800; }
.compact-id { color:var(--text); font-size:14px; font-weight:900; margin-top:4px; }
.compact-title { color:var(--muted); font-size:11.5px; margin-top:1px; line-height:1.3; }
.compact-score-ring { width:42px; height:42px; border-radius:999px; background:conic-gradient(var(--green) var(--score), #f1f5f9 0); display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.compact-score-inner { width:32px; height:32px; border-radius:999px; background:white; display:flex; align-items:center; justify-content:center; color:var(--text); font-size:11px; font-weight:900; }
.compact-chips { margin-top:8px; }
.compact-chips .chip { font-size:10.5px; padding:4px 9px; margin:2px 3px 0 0; }

/* ---- footer (true anchor links) ---- */
.fixed-footer-spacer { height:60px; }
.fixed-footer {
    position: fixed;
    bottom:0; left:0; right:0;
    background:white;
    border-top:1px solid #e5e7eb;
    padding:6px 14px;
    z-index:9999;
}
.fixed-footer-inner { max-width:720px; margin:auto; display:flex; justify-content:space-around; align-items:center; }
.footer-link {
    flex: 1;
    text-align: center;
    color: var(--muted);
    font-weight: 650;
    font-size: 12.5px;
}
.fixed-footer .stButton > button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: var(--muted) !important;
    font-weight: 650 !important;
    font-size: 12.5px !important;
    text-decoration: none !important;
    min-height: 38px !important;
    padding: 2px !important;
}
.fixed-footer .stButton > button:hover {
    color: var(--indigo) !important;
    text-decoration: underline !important;
    background: transparent !important;
}
.fixed-footer .stButton > button:focus { box-shadow: none !important; }
.stButton > button { border-radius:14px; font-weight:780; min-height:44px; }
@media (max-width:700px) { .hero-title{font-size:46px;} .panel-grid{grid-template-columns:repeat(2,1fr);} .feature-row{gap:18px;} }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def init_state():
    defaults = {
        "screen": "landing",
        "blueprint": None,
        "results": None,
        "selected_idx": 0,
        "jd_file": None,
        "cand_file": None,
        "scanned_count": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def set_screen(screen: str):
    st.session_state.screen = screen


init_state()


def top_nav():
    st.markdown('<div class="top-nav-wrap"><div class="top-nav-inner">', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown('<div class="brand"><div class="brand-icon">⚡</div>HireFormer</div>', unsafe_allow_html=True)
    with c2:
        if st.button("Demo Mode", key="header_demo", use_container_width=True):
            st.session_state.jd_file = None
            st.session_state.cand_file = None
            set_screen("processing")
            st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)


def load_uploaded_docx(uploaded):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(uploaded.getvalue())
        return load_docx_text(tmp.name)


def save_uploaded_file(uploaded, suffix):
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getvalue())
        return tmp.name
def count_jsonl_lines(path):
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


@st.cache_data(show_spinner=False)
def run_demo():
    # jd_text = load_docx_text("data/job_description.docx")
    # blueprint = build_hiring_blueprint(jd_text)

    # results = fast_rank_candidates_from_jsonl(
    #     "data/candidates.jsonl",
    #     blueprint,
    #     shortlist_size=5000
    # )

    #return blueprint, results
    jd_text = load_docx_text("data/job_description.docx")
    blueprint = build_hiring_blueprint(jd_text)

    candidates = load_sample_json("data/sample_candidates.json")
    results = rank_candidates(candidates, blueprint)

    return blueprint, results, len(candidates)


def run_uploaded(jd_file, cand_file):
    jd_text = load_uploaded_docx(jd_file)
    blueprint = build_hiring_blueprint(jd_text)

    if cand_file.name.endswith(".jsonl"):
        path = save_uploaded_file(cand_file, ".jsonl")
        scanned_count = count_jsonl_lines(path)

        results = fast_rank_candidates_from_jsonl(
            path,
            blueprint,
            shortlist_size=5000
        )
    else:
        raw = cand_file.getvalue().decode("utf-8")
        candidates = json.loads(raw)
        scanned_count = len(candidates)
        results = rank_candidates(candidates, blueprint)

    return blueprint, results, scanned_count


def processing():
    st.markdown("<div style='height:70px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;">
        <div style="width:70px;height:70px;border-radius:22px;background:#4f46e5;color:white;display:flex;align-items:center;justify-content:center;font-size:32px;margin:auto;">⚡</div>
        <h2 style="color:#111827;margin-top:24px;">HireFormer is thinking...</h2>
        <p style="color:#9ca3af;">Transformer-inspired hiring analysis in progress</p>
    </div>
    """, unsafe_allow_html=True)
    steps = ["Reading Job Description", "Understanding hiring intent", "Building ideal candidate profile", "Extracting candidate evidence", "Running hiring panel", "Building shortlist"]
    progress = st.progress(0)
    box = st.empty()
    for i, step in enumerate(steps):
        box.markdown(f"**{step}...**")
        progress.progress((i + 1) / len(steps))
        time.sleep(0.35)
    if st.session_state.jd_file and st.session_state.cand_file:
        blueprint, results, scanned_count = run_uploaded(
            st.session_state.jd_file,
            st.session_state.cand_file
        )
    else:
        blueprint, results, scanned_count = run_demo()

    st.session_state.blueprint = blueprint
    st.session_state.results = results
    st.session_state.scanned_count = scanned_count
    set_screen("blueprint")
    st.rerun()


def landing():
    top_nav()
    st.markdown("""
    <div class="hero">
        <div class="hero-badge">● Transformer-Inspired Hiring Intelligence</div>
        <div class="hero-title">Hire<span>Former</span></div>
        <div class="hero-sub">Upload a Job Description. Upload Candidate Profiles.</div>
        <div class="word-strip"><b>Understand</b><span>·</span><b>Evaluate</b><span>·</span><b>Rank</b><span>·</span><b>Explain</b></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="upload-box">', unsafe_allow_html=True)
    jd_file = st.file_uploader("📄 Upload Job Description", type=["docx"], help="Upload the job description DOCX file.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="upload-box">', unsafe_allow_html=True)
    cand_file = st.file_uploader("👥 Upload Candidate Profiles", type=["json", "jsonl"], help="Upload candidates JSON or JSONL file.")
    st.markdown('</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Run HireFormer", disabled=not (jd_file and cand_file), use_container_width=True, key="landing_run"):
            st.session_state.jd_file = jd_file
            st.session_state.cand_file = cand_file
            set_screen("processing")
            st.rerun()
    with c2:
        if st.button("Demo Mode", use_container_width=True, key="landing_demo"):
            st.session_state.jd_file = None
            st.session_state.cand_file = None
            set_screen("processing")
            st.rerun()

    st.markdown("""
    <div class="feature-row">
        <div class="feature"><div class="feature-icon">📋</div><div class="feature-title">Hiring Blueprint</div><div class="feature-desc">Understand the role</div></div>
        <div class="feature"><div class="feature-icon">🏆</div><div class="feature-title">Leaderboard</div><div class="feature-desc">Ranked candidates</div></div>
    </div>
    """, unsafe_allow_html=True)


def blueprint_page():
    b = st.session_state.blueprint
    st.markdown('<div class="badge">⚡ Hiring Blueprint</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Here’s what HireFormer understood</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Parsed from your Job Description using the JD Intelligence Engine.</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="card"><div class="card-title">Target Role</div><h3 style="color:#111827;">{b.role}</h3><p style="color:#6b7280;">AI / ML Infrastructure · 5–9 years</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="card"><div class="card-title">Mission</div><p style="color:#374151;line-height:1.6;">{b.core_mission}</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="card"><div class="card-title">Required Skills</div>' + ''.join([f"<span class='chip green'>{x}</span>" for x in b.required_skills]) + '</div>', unsafe_allow_html=True)
    st.markdown('<div class="card"><div class="card-title">Expected Behaviors</div>' + ''.join([f"<span class='chip indigo'>{x}</span>" for x in b.behavioral_traits]) + '</div>', unsafe_allow_html=True)
    st.markdown('<div class="card"><div class="card-title">Risk Signals / Disqualifiers</div>' + ''.join([f"<span class='chip red'>{x}</span>" for x in b.disqualifiers]) + '</div>', unsafe_allow_html=True)
    if st.button("Continue to Leaderboard →", use_container_width=True, key="blueprint_continue"):
        set_screen("leaderboard")
        st.rerun()


def rank_icon(rank: int) -> str:
    return "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"


def candidate_card(result: Dict[str, Any], idx: int, show_button: bool = True):
    p = result["candidate"].get("profile", {})
    score = round(result["score"])
    risk = "Low Risk" if not result["risk_flags"] else "Review Risk"
    risk_class = "green" if not result["risk_flags"] else "red"
    fit = "Excellent Fit" if score >= 75 else "Strong Fit" if score >= 60 else "Review"
    st.markdown(f"""
    <div class="candidate-card">
        <div class="candidate-top">
            <div class="rank-icon">{rank_icon(result['rank'])}</div>
            <div class="score-ring" style="--score:{score}%;"><div class="score-inner">{score}</div></div>
            <div style="flex:1;">
                <div style="display:flex;justify-content:space-between;gap:12px;">
                    <div><div class="candidate-id">{result['candidate_id']}</div><div class="candidate-title">{p.get('current_title','Candidate')}</div></div>
                    <span class="chip {risk_class}">{risk}</span>
                </div>
                <div style="margin-top:8px;"><span style="color:#f59e0b;">★★★★★</span><span style="font-size:12px;font-weight:700;color:#6b7280;margin-left:8px;">{fit}</span></div>
                <div class="reason">{generate_reasoning(result['candidate'], result)[:175]}...</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if show_button and st.button("View Profile", key=f"view_{idx}", use_container_width=True):
        st.session_state.selected_idx = idx
        set_screen("candidate")
        st.rerun()


def leaderboard_page():
    results = st.session_state.results
    st.markdown('<div class="badge">🏆 Candidate Leaderboard</div>', unsafe_allow_html=True)
    scanned_count = st.session_state.get("scanned_count", len(results))
    shortlisted_count = len(results)
    final_count = min(100, len(results))

    #st.markdown('<div class="badge">🏆 Candidate Leaderboard</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:10px 0 20px;">
        <div class="card" style="padding:16px;text-align:center;margin-bottom:0;">
            <div style="font-size:24px;font-weight:950;color:#111827;">{scanned_count:,}</div>
            <div style="font-size:11px;font-weight:850;color:#9ca3af;text-transform:uppercase;">Candidates Scanned</div>
        </div>
        <div class="card" style="padding:16px;text-align:center;margin-bottom:0;">
            <div style="font-size:24px;font-weight:950;color:#111827;">{shortlisted_count:,}</div>
            <div style="font-size:11px;font-weight:850;color:#9ca3af;text-transform:uppercase;">Shortlisted</div>
        </div>
        <div class="card" style="padding:16px;text-align:center;margin-bottom:0;">
            <div style="font-size:24px;font-weight:950;color:#111827;">{final_count}</div>
            <div style="font-size:11px;font-weight:850;color:#9ca3af;text-transform:uppercase;">Final Ranking</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="page-subtitle">Senior AI Engineer · AI / ML Infrastructure</div>', unsafe_allow_html=True)
    if st.button("Compare Candidates", use_container_width=True, key="leaderboard_compare"):
        set_screen("compare")
        st.rerun()
    max_show = min(100, len(results))
    num_to_show = st.slider("Candidates to display", 10, max_show, max_show)

    for i, r in enumerate(results[:num_to_show]):
        candidate_card(r, i)


def radar(result: Dict[str, Any]):
    vector = result["candidate_vector"]
    labels = [k.replace("_", " ").title() for k in vector]
    values = [round(v * 100, 1) for v in vector.values()]
    labels.append(labels[0]); values.append(values[0])
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=labels, fill="toself", line=dict(color="#6366f1", width=2), fillcolor="rgba(99,102,241,0.16)"))
    fig.update_layout(height=300, margin=dict(l=25, r=25, t=25, b=25), paper_bgcolor="white", plot_bgcolor="white", font=dict(color="#374151", size=11), polar=dict(bgcolor="white", radialaxis=dict(visible=True, range=[0,100], gridcolor="#e5e7eb"), angularaxis=dict(gridcolor="#f3f4f6")), showlegend=False)
    return fig


def candidate_page():
    r = st.session_state.results[st.session_state.selected_idx]
    p = r["candidate"].get("profile", {})
    score = round(r["score"])
    # Plain header (no card wrapper) — this replaces the extra white card that used to float on top
    st.markdown(f"""
    <div class="plain-header">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div><h2 style="color:#111827;margin-bottom:4px;">{r['candidate_id']}</h2><p style="color:#6b7280;">{p.get('current_title','Candidate')} · {p.get('years_of_experience',0)} yrs · {p.get('location','')}</p></div>
            <div class="score-ring" style="--score:{score}%;"><div class="score-inner">{score}%</div></div>
        </div>
        <hr style="border:none;border-top:1px solid #eef2f7;margin:16px 0;">
        <p style="color:#374151;line-height:1.65;">{generate_reasoning(r['candidate'], r)}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Candidate DNA</div>', unsafe_allow_html=True)
    st.plotly_chart(radar(r), use_container_width=True)

    st.markdown('<div class="section-title">Hiring Panel</div>', unsafe_allow_html=True)
    panel = r["panel_scores"]
    st.markdown(f"""
    <div class="panel-grid">
        <div class="panel-box"><div>🧠</div><div class="panel-role">ML Lead</div><div class="panel-score">{round(panel.get('ml_lead',0))}</div></div>
        <div class="panel-box"><div>👤</div><div class="panel-role">Recruiter</div><div class="panel-score">{round(panel.get('recruiter',0))}</div></div>
        <div class="panel-box"><div>🚀</div><div class="panel-role">Product Lead</div><div class="panel-score">{round(panel.get('product_lead',0))}</div></div>
        <div class="panel-box"><div>🛡️</div><div class="panel-role">Risk Auditor</div><div class="panel-score">{round(panel.get('risk_auditor',0))}</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Evidence Graph</div>', unsafe_allow_html=True)
    evidence = r.get("evidence_nodes", [])
    if evidence:
        st.markdown(''.join([f"<span class='chip green'>{e['label'].title()} · {e['strength']}</span>" for e in evidence[:8]]), unsafe_allow_html=True)
    else:
        st.markdown('<span class="chip gray">No strong evidence nodes found</span>', unsafe_allow_html=True)
    if r["risk_flags"]:
        st.markdown('<div class="section-title" style="margin-top:18px;">Risk Assessment</div>', unsafe_allow_html=True)
        st.markdown(''.join([f"<span class='chip red'>⚠ {x}</span>" for x in r['risk_flags']]), unsafe_allow_html=True)


def compact_candidate_card(result: Dict[str, Any]):
    p = result["candidate"].get("profile", {})
    score = round(result["score"])
    risk = "Low Risk" if not result["risk_flags"] else "Review Risk"
    risk_class = "green" if not result["risk_flags"] else "red"
    fit = "Excellent Fit" if score >= 75 else "Strong Fit" if score >= 60 else "Review"
    st.markdown(f"""
    <div class="candidate-card-compact">
        <div class="compact-top-row">
            <div>
                <div class="compact-rank">{rank_icon(result['rank'])}</div>
                <div class="compact-id">{result['candidate_id']}</div>
                <div class="compact-title">{p.get('current_title','Candidate')}</div>
            </div>
            <div class="compact-score-ring" style="--score:{score}%;"><div class="compact-score-inner">{score}</div></div>
        </div>
        <div class="compact-chips">
            <span class="chip {risk_class}">{risk}</span>
            <span class="chip gray">{fit}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def compare_page():
    results = st.session_state.results[:10]
    st.markdown('<div class="badge">⚖ Compare Candidates</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Head-to-Head Analysis</div>', unsafe_allow_html=True)
    labels = [f"#{r['rank']} {r['candidate_id']} — {r['candidate']['profile'].get('current_title','')}" for r in results]
    a_idx = st.selectbox("Candidate A", range(len(labels)), index=0, format_func=lambda i: labels[i], key="compare_a")
    b_idx = st.selectbox("Candidate B", range(len(labels)), index=1 if len(labels) > 1 else 0, format_func=lambda i: labels[i], key="compare_b")
    a, b = results[a_idx], results[b_idx]
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        compact_candidate_card(a)
        st.plotly_chart(radar(a), use_container_width=True)
    with col2:
        compact_candidate_card(b)
        st.plotly_chart(radar(b), use_container_width=True)
    winner = a if a["score"] >= b["score"] else b
    st.success(f"Recommended winner: {winner['candidate_id']} with score {round(winner['score'], 2)}")


def export_page():
    st.markdown('<div class="badge">📄 Export Reports</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Export & Download</div>', unsafe_allow_html=True)
    all_results = st.session_state.results
    if len(all_results) < 100:
        st.info(f"Only {len(all_results)} candidates were ranked by the engine, so the export contains all {len(all_results)} instead of 100. Check the candidate-ranking step (src/ranker.py) if you expected more.")
    rows = [{"candidate_id": r["candidate_id"], "rank": r["rank"], "score": r["score"], "reasoning": generate_reasoning(r["candidate"], r)} for r in all_results[:100]]
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"), "hireformer_top100.csv", "text/csv", use_container_width=True)


def bottom_nav():
    if st.session_state.screen in ["landing", "processing"]:
        return
    st.markdown('<div class="fixed-footer-spacer"></div><div class="fixed-footer"><div class="fixed-footer-inner">', unsafe_allow_html=True)
    cols = st.columns(4)
    items = [("Blueprint", "blueprint"), ("Rankings", "leaderboard"), ("Export", "export"), ("Reset", "landing")]
    for col, (label, target) in zip(cols, items):
        with col:
            if st.button(label, use_container_width=True, key=f"nav_{target}"):
                if target == "landing":
                    st.session_state.results = None
                    st.session_state.blueprint = None
                set_screen(target)
                st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)


screen = st.session_state.screen
if screen == "landing": landing()
elif screen == "processing": processing()
elif screen == "blueprint": blueprint_page()
elif screen == "leaderboard": leaderboard_page()
elif screen == "candidate": candidate_page()
elif screen == "compare": compare_page()
elif screen == "export": export_page()
else: landing()

bottom_nav()