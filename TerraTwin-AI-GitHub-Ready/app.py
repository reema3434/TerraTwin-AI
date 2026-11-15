from pathlib import Path
import json
import pandas as pd
import streamlit as st
from integration_pipeline import run_full_analysis

try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    px = None
    go = None

# -------------------------------------------------------------------
# PAGE CONFIGURATION AND THEME
# -------------------------------------------------------------------

st.set_page_config(
    page_title="TerraTwin AI",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

NAVY = "#101D35"
PANEL = "#1B2B49"
CYAN = "#D69AB0"
BLUE = "#8B2252"
MUTED = "#B8B6C4"
WHITE = "#F4F2F3"

st.markdown(
    f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, {NAVY} 0%, #172743 60%, #1B2B49 100%);
        color: {WHITE};
    }}
    [data-testid="stSidebar"] {{
        display: none;
    }}
    h1, h2, h3 {{
        color: {WHITE};
    }}
    p, label, .stCaption {{
        color: {MUTED};
    }}
    div.stButton > button {{
        background: {BLUE};
        color: white;
        border: 1px solid {CYAN};
        border-radius: 9px;
        padding: 0.65rem 1.1rem;
        font-weight: 650;
        transition: all .2s ease;
    }}
    div.stButton > button:hover {{
        background: #9C6685;
        border-color: #E99A83;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(56,189,248,.18);
    }}
    div[data-testid="stMetric"] {{
        background: {PANEL};
        border: 1px solid #1B3B59;
        border-radius: 12px;
        padding: 15px;
    }}
    div[data-testid="stMetric"] label {{
        color: {MUTED};
    }}
    .eyebrow {{
        color: {CYAN};
        letter-spacing: 3px;
        font-size: 0.76rem;
        font-weight: 700;
    }}
    .hero-title {{
        color: {WHITE};
        font-size: clamp(2.7rem, 6vw, 5rem);
        font-weight: 850;
        line-height: 1.05;
        margin: 0.5rem 0 1rem 0;
    }}
    .hero-copy {{
        color: #B7C8D9;
        font-size: 1.12rem;
        line-height: 1.8;
        max-width: 780px;
    }}
    .panel {{
        background: {PANEL};
        border: 1px solid #1B3B59;
        border-radius: 14px;
        padding: 1.1rem 1.25rem;
        min-height: 130px;
    }}
    .panel-title {{
        color: {WHITE};
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 0.45rem;
    }}
    .panel-copy {{
        color: {MUTED};
        font-size: 0.92rem;
        line-height: 1.6;
    }}
    .brand-name {{font-size:1.12rem;font-weight:800;color:#F3F7FB;}}
    .brand-sub {{font-size:.68rem;letter-spacing:2px;color:#B8B6C4;}}
    .planet-hero {{border:1px solid #245276;border-radius:20px;padding:18px;
      background:radial-gradient(circle at 70% 30%,rgba(56,189,248,.13),transparent 35%),
      linear-gradient(135deg,#0B2038,#071426);box-shadow:0 18px 50px rgba(0,0,0,.22);}}
    .glow-label {{color:#E99A83;letter-spacing:2px;font-size:.72rem;font-weight:750;}}
    .section-kicker {{
        color: #E99A83;
        font-size: .72rem;
        font-weight: 800;
        letter-spacing: 2px;
        margin-top: 1.1rem;
    }}
    .section-heading {{
        color: #F4F2F3;
        font-size: 1.45rem;
        font-weight: 750;
        margin: .15rem 0 .2rem 0;
    }}
    .section-description {{
        color: #B8B6C4;
        font-size: .92rem;
        margin-bottom: .8rem;
    }}
    .selection-summary {{
        margin-top: 1.1rem;
        padding: 14px 16px;
        border-radius: 12px;
        border: 1px solid rgba(214,154,176,.32);
        background: rgba(214,154,176,.08);
    }}
    .summary-label {{
        color: #E99A83;
        font-size: .7rem;
        font-weight: 800;
        letter-spacing: 1.4px;
        margin-bottom: 8px;
    }}
    .feature-chip-wrap {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }}
    .feature-chip {{
        display: inline-block;
        padding: 6px 11px;
        border-radius: 999px;
        background: rgba(233,154,131,.13);
        border: 1px solid rgba(233,154,131,.4);
        color: #F4F2F3;
        font-size: .82rem;
    }}
    .score-hero {{border:1px solid #28749A;border-radius:18px;padding:22px;
     background:linear-gradient(120deg,#243653,#1B2B49 65%,#101D35);}}
    .score-placeholder {{font-size:2.5rem;font-weight:800;color:#E99A83;line-height:1.1;}}
    .api-placeholder {{border:1px dashed #B77F9E;border-radius:12px;padding:14px;
     background:rgba(10,35,56,.55);min-height:115px;margin-bottom:10px;}}
    .api-label {{font-size:.72rem;letter-spacing:1.2px;color:#E99A83;font-weight:700;}}
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# DATA HELPERS
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SITES_FILE = DATA_DIR / "saudi_sites.csv"
TERRAIN_FILE = DATA_DIR / "terrain_candidates.csv"
FALLBACK_TERRAIN_FILE = BASE_DIR / "terrain_data.csv"

TERRAIN_COLUMNS = [
    "region",
    "body",
    "slope_deg",
    "roughness_m",
    "local_relief_m",
]

@st.cache_data
def load_csv(path_string: str):
    path = Path(path_string)
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception as exc:
        st.warning(f"Could not read {path.name}: {exc}")
        return None

def load_sites():
    df = load_csv(str(SITES_FILE))
    if df is None:
        return None
    required = {"site_name", "latitude", "longitude"}
    missing = required - set(df.columns)
    if missing:
        return None
    df = df.copy()
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    return df.dropna(subset=["latitude", "longitude"])

def load_terrain_candidates():
    df = load_csv(str(TERRAIN_FILE))
    if df is None:
        df = load_csv(str(FALLBACK_TERRAIN_FILE))
    if df is None:
        return None
    missing = set(TERRAIN_COLUMNS) - set(df.columns)
    if missing:
        return None
    return df

def make_map(df):
    if px is None:
        st.info("Install Plotly to display the interactive map: pip install plotly")
        return
    fig = px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        hover_name="site_name",
        hover_data=[col for col in ["region", "body"] if col in df.columns],
        zoom=4.2,
        height=520,
        color_discrete_sequence=[CYAN],
    )
    fig.update_layout(
        mapbox_style="carto-darkmatter",
        mapbox_center={"lat": 24.0, "lon": 45.0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        font_color=WHITE,
    )
    st.plotly_chart(fig, use_container_width=True)

def render_planetary_twin_logo():
    """Display the official Planetary Twin logo supplied by the team."""
    logo_path = Path(__file__).parent / "assets" / "planetary_twin_logo.png"
    if logo_path.exists():
        st.image(str(logo_path), width=190)
    else:
        # رسم الشعار تلقائياً بنفس الشكل إذا لم تكن الصورة مرفوعة في مجلد assets
        st.markdown(
            """
            <div style="text-align:center; width:150px;">
                <svg width="90" height="75" viewBox="0 0 100 85" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M35 45 C45 25, 65 20, 75 22" stroke="#B77F9E" stroke-width="2" stroke-dasharray="3 3"/>
                    <path d="M40 58 C55 55, 70 42, 78 30" stroke="#B77F9E" stroke-width="2"/>
                    <circle cx="78" cy="24" r="9" fill="#E99A83"/>
                    <circle cx="28" cy="54" r="16" fill="#F4F2F3"/>
                    <path d="M13 54 H43 M15 60 H41 M18 65 H38" stroke="#1B2B49" stroke-width="2.5"/>
                </svg>
                <div style="color:#F4F2F3; font-weight:700; font-size:1.05rem; margin-top:2px;">Planetary Twin</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_brand_bar():
    logo_col, title_col, event_col = st.columns([1.0, 2.2, 1.5], vertical_alignment="center")
    with logo_col:
        render_planetary_twin_logo()
    with title_col:
        st.markdown(
            '<div class="brand-name">TerraTwin <span style="color:#E99A83">AI</span></div>'
            '<div class="brand-sub">PLANETARY TWIN · GEOSPATIAL INTELLIGENCE</div>',
            unsafe_allow_html=True,
        )
    with event_col:
        st.markdown(
            """
            <div style="display:flex;flex-direction:column;align-items:flex-end;gap:7px;">
              <div style="background:#F7F7F7;border-radius:9px;padding:7px 10px;
                          display:inline-flex;align-items:center;justify-content:center;
                          max-width:220px;">
                <img
                  src="https://upload.wikimedia.org/wikipedia/commons/2/27/NASA_Space_Apps_Default_Logo_2-Color_Black.svg"
                  alt="NASA Space Apps Challenge"
                  style="display:block;width:100%;max-width:190px;height:auto;"
                />
              </div>
              <div style="text-align:right;color:#B8B6C4;letter-spacing:1px;
                          font-size:.66rem;line-height:1.5;">
                2026 PARTICIPANT PROJECT<br>
                <span style="letter-spacing:0;color:#9A8FA3;">
                  Independent student prototype · Uses NASA open data
                </span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.divider()

def render_page_navigation():
    n1, n2, n3, n4 = st.columns(4)
    with n1:
        st.button("← Welcome", key=f"welcome_nav_{st.session_state.navigation}",
                  on_click=go_to, args=("Welcome Page",), use_container_width=True)
    with n2:
        st.button("Mission Control", key=f"control_nav_{st.session_state.navigation}",
                  on_click=go_to, args=("Mission Control",), use_container_width=True)
    with n3:
        st.button("Mission Setup", key=f"setup_nav_{st.session_state.navigation}",
                  on_click=go_to, args=("Mission Configuration",), use_container_width=True)
    with n4:
        st.button("Mission Test Lab 🔬", key=f"lab_nav_{st.session_state.navigation}",
                  on_click=go_to, args=("Mission Test Lab",), use_container_width=True)

def render_interactive_globe(height=520):
    if go is None:
        return
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(
        lon=[37.92, 39.96], lat=[26.60, 25.73], mode="markers+text",
        text=["AlUla", "Harrat Khaybar"],
        textposition="top right",
        marker={"size": 8, "color": "#E99A83"},
        showlegend=False,
    ))
    fig.update_geos(
        projection_type="orthographic",
        projection_rotation={"lon": 38, "lat": 24, "roll": 0},
        showland=True,
        landcolor="#E8D9CA",
        showocean=True,
        oceancolor="#263F60",
        showcountries=True,
        countrycolor="#B77F9E",
        showcoastlines=True,
        coastlinecolor="#E99A83",
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#F4F2F3",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------------------------
# SESSION STATE AND NAVIGATION
# -------------------------------------------------------------------
if "navigation" not in st.session_state:
    st.session_state.navigation = "Welcome Page"
if "mission" not in st.session_state:
    st.session_state.mission = {
        "target_body": "Moon",
        "target_region": "Connecting_Ridge",
        "mission_type": "Mobility",
        "parameters": ["slope_deg", "roughness_m", "local_relief_m", "slope_std_deg"],
    }

def go_to(page_name):
    st.session_state.navigation = page_name

def reset_region_for_body_change():
    st.session_state["mission_target_region_widget"] = (
        "Connecting_Ridge" if st.session_state.get("mission_target_body_widget") == "Moon"
        else "Athabasca_Valles"
    )

def save_mission_and_open_results():
    # 1. Read values directly from manual UI dropdown selections only
    body = st.session_state.get("mission_target_body_widget", "Moon")
    region = st.session_state.get("mission_target_region_widget", "Connecting_Ridge")
    objective = st.session_state.get("mission_type_widget", "Mobility")

    objective_features = {
        "Mobility": ["slope_deg", "roughness_m", "local_relief_m", "slope_std_deg"],
        "Navigation": ["roughness_m", "local_relief_m", "slope_std_deg"],
        "Robotic Operations": ["slope_deg", "roughness_m", "flat_fraction"],
    }
    parameters = objective_features.get(objective, ["slope_deg", "roughness_m", "local_relief_m", "slope_std_deg"])

    st.session_state.configuration_error = ""
    st.session_state.mission = {
        "target_body": body,
        "target_region": region,
        "mission_type": objective,
        "analysis_type": "mission_objective",
        "parameters": parameters,
    }

    # 2. Run analysis based on manual options without any prompt
    st.session_state.analysis_result = run_full_analysis(
        target_body=body,
        target_region=region,
        mission_type=objective,
        parameters=parameters,
        user_query="",  # Completely empty since prompt was removed
    )
    st.session_state.navigation = "Similarity Results"

# -------------------------------------------------------------------
# PAGES
# -------------------------------------------------------------------

def show_welcome_page():
    render_brand_bar()
    left, right = st.columns([1.05, 1.15], gap="large")
    with left:
        st.markdown('<div class="eyebrow">PLANETARY TERRAIN INTELLIGENCE</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-title">Earth is our<br><span style="color:#D69AB0;">testing ground.</span></div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="hero-copy">
        Discover terrestrial landscapes in Saudi Arabia that share measurable terrain characteristics
        with the Moon and Mars. Explore planetary data, compare terrain, and support
        mission planning with evidence.
        </div>""", unsafe_allow_html=True)
        st.markdown("""
        <div style="display:flex;gap:9px;flex-wrap:wrap;margin:18px 0 22px;">
          <span class="glow-label">SRTM · EARTH</span><span style="color:#45627C">/</span>
          <span class="glow-label">LOLA · MOON</span><span style="color:#45627C">/</span>
          <span class="glow-label">HRSC · MARS</span>
        </div>""", unsafe_allow_html=True)
        st.button("Launch Mission Control  →", use_container_width=True, type="primary",
                  on_click=go_to, args=("Mission Control",))
    with right:
        st.markdown('<div class="planet-hero">', unsafe_allow_html=True)
        st.markdown('<div class="glow-label">INTERACTIVE EARTH GLOBE · DRAG TO ROTATE · SCROLL TO ZOOM</div>', unsafe_allow_html=True)
        render_interactive_globe(height=480)
        st.markdown('</div>', unsafe_allow_html=True)

def show_mission_control():
    render_brand_bar()
    render_page_navigation()
    st.title("Mission Control")
    st.caption("TerraTwin AI · Geospatial overview (75 m Resolution · 4 Study Regions)")

    sites = load_sites()
    terrain = load_terrain_candidates()

    m1, m2, m3 = st.columns(3)
    m1.metric("Mapped Saudi Analog Sites", len(sites) if sites is not None else 0)
    m2.metric("Verified Study Regions", len(terrain) if terrain is not None else 0)
    m3.metric("Target Bodies", "Moon / Mars")

    st.write("")
    left, right = st.columns([2.2, 1])
    with left:
        st.subheader("Saudi Arabia · Study Regions (AlUla & Harrat Khaybar)")
        if sites is not None and not sites.empty:
            make_map(sites)
    with right:
        st.subheader("Analysis Workflow")
        st.markdown(
            """
            1. Select a target body (`Moon` or `Mars`) and reference region.
            2. Or describe your mission goal in natural language for AI classification.
            3. Run the similarity engine (`main.py`).
            4. Review AI scientific explanations & feature contributions.
            5. Inspect hybrid terrain difficulty in **Mission Test Lab**.
            """
        )
        st.button("Start Mission Setup  →", use_container_width=True, on_click=go_to, args=("Mission Configuration",))

def show_mission_configuration():
    render_brand_bar()
    render_page_navigation()
    st.title("Mission Configuration")
    st.caption("Define the planetary reference and choose how you want to compare terrain.")

    current = st.session_state.mission
    if "mission_target_body_widget" not in st.session_state:
        st.session_state.mission_target_body_widget = current.get("target_body", "Moon")
    if "mission_target_region_widget" not in st.session_state:
        st.session_state.mission_target_region_widget = current.get("target_region") or "Connecting_Ridge"
    if "mission_type_widget" not in st.session_state:
        st.session_state.mission_type_widget = current.get("mission_type") or "Mobility"
    if "analysis_mode_widget" not in st.session_state:
        st.session_state.analysis_mode_widget = (
            "Terrain parameters only" if current.get("analysis_type") == "terrain_parameters_only"
            else "Mission objective"
        )

    # AI Natural Language Box (Stage 1)
    st.markdown(
        '<div class="section-kicker">OPTIONAL · AI MISSION UNDERSTANDING (STAGE 1)</div>'
        '<div class="section-heading">',
        unsafe_allow_html=True,
    )


    st.markdown(
        '<div class="section-kicker">STEP 01</div>'
        '<div class="section-heading">Target environment</div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        env_left, env_right = st.columns(2, gap="large")
        with env_left:
            body = st.selectbox(
                "Planetary body",
                ["Moon", "Mars"],
                key="mission_target_body_widget",
                on_change=reset_region_for_body_change,
            )
        regions = (
            ["Connecting_Ridge"] if body == "Moon" else ["Athabasca_Valles"]
        )
        if st.session_state.mission_target_region_widget not in regions:
            st.session_state.mission_target_region_widget = regions[0]
        with env_right:
            st.selectbox("Reference region (Official 75m GIS Dataset)", regions, key="mission_target_region_widget")

    st.markdown(
        '<div class="section-kicker">STEP 02</div>'
        '<div class="section-heading">Choose your comparison approach</div>',
        unsafe_allow_html=True,
    )
    mode = st.radio(
        "Analysis approach",
        ["Mission objective", "Terrain parameters only"],
        horizontal=True,
        key="analysis_mode_widget",
        label_visibility="collapsed",
    )

    if mode == "Mission objective":
        with st.container(border=True):
            st.selectbox(
                "Select mission objective",
                ["Mobility", "Navigation", "Robotic Operations"],
                key="mission_type_widget",
            )
            objective_features = {
                "Mobility": [
                    ("Mean slope", "slope_deg"),
                    ("Surface roughness", "roughness_m"),
                    ("Local relief", "local_relief_m"),
                    ("Slope variability", "slope_std_deg"),
                ],
                "Navigation": [
                    ("Surface roughness", "roughness_m"),
                    ("Local relief", "local_relief_m"),
                    ("Slope variability", "slope_std_deg"),
                ],
                "Robotic Operations": [
                    ("Mean slope", "slope_deg"),
                    ("Surface roughness", "roughness_m"),
                    ("Flat fraction", "flat_fraction"),
                ],
            }
            selected_objective = st.session_state.mission_type_widget
            feature_labels = objective_features[selected_objective]
            chips = "".join(f'<span class="feature-chip">{label}</span>' for label, _ in feature_labels)
            st.markdown(
                f'<div class="selection-summary"><div class="summary-label">FEATURES INCLUDED (EQUAL WEIGHTS)</div>'
                f'<div class="feature-chip-wrap">{chips}</div></div>',
                unsafe_allow_html=True,
            )
    else:
        available_features = {
            "Mean slope (slope_deg)": "slope_deg",
            "Surface roughness (roughness_m)": "roughness_m",
            "Local relief (local_relief_m)": "local_relief_m",
            "Slope variability (slope_std_deg)": "slope_std_deg",
            "Flat fraction (flat_fraction)": "flat_fraction",
        }
        with st.container(border=True):
            chosen_labels = st.multiselect(
                "Select terrain comparison parameters",
                list(available_features.keys()),
                default=["Mean slope (slope_deg)", "Surface roughness (roughness_m)", "Local relief (local_relief_m)"],
                key="custom_parameter_labels_widget",
            )
            st.session_state.custom_parameters_widget = [available_features[label] for label in chosen_labels]

    if st.session_state.get("configuration_error"):
        st.error(st.session_state.configuration_error)

    st.write("")
    back_col, spacer_col, run_col = st.columns([1, 0.15, 1])
    with back_col:
        st.button("← Back", on_click=go_to, args=("Mission Control",), use_container_width=True)
    with run_col:
        st.button("Run Analysis & View Results →", type="primary", on_click=save_mission_and_open_results, use_container_width=True)

def show_similarity_results():
    render_brand_bar()
    render_page_navigation()
    st.title("Similarity Results")
    st.caption("Feature-level similarity, evidence-based justifications, and overall score")

    result = st.session_state.get("analysis_result")
    if not isinstance(result, dict):
        result = run_full_analysis()
        st.session_state.analysis_result = result

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Target Body", result.get("target_body", "Moon"))
    c2.metric("Reference Region", result.get("target_region", "Connecting_Ridge"))
    c3.metric("Mission Mode", result.get("mission_type", "Mobility"))
    c4.metric("🏆 Top Saudi Analog", result.get("best_earth_region", "AlUla"))

    if result.get("ai_classification"):
        st.success(f"🤖 **AI Stage 1 Classification:** `{json.dumps(result['ai_classification'])}`")

    st.markdown("### Overall similarity score")
    total_score = result.get("total_similarity_percentage")
    st.metric(f"Overall Similarity ({result.get('best_earth_region')} vs. {result.get('target_region')})", f"{total_score:.2f}%")

    feature_names = {
        "slope_deg": "Mean slope (°)",
        "roughness_m": "Mean roughness (m)",
        "local_relief_m": "Mean local relief (m)",
        "slope_std_deg": "Slope variability (°)",
        "flat_fraction": "Flat fraction",
    }
    features = result.get("selected_features", ["slope_deg", "roughness_m", "local_relief_m"])

    st.markdown("### Individual feature scores")
    feature_scores = result.get("feature_scores", {})
    columns = st.columns(2)
    for index, feature in enumerate(features):
        score_data = feature_scores.get(feature, {})
        percentage = score_data.get("percentage")
        justification = score_data.get("justification", "")
        with columns[index % 2]:
            score_text = f"{percentage:.2f}%" if isinstance(percentage, (int, float)) else "— %"
            st.markdown(f'''<div class="api-placeholder"><div class="api-label">{feature_names.get(feature, feature).upper()}</div>
            <div class="score-placeholder" style="font-size:2rem;">{score_text}</div>
            <div style="color:#C9C3CE;font-size:.86rem;margin-top:8px;"><b>Justification</b><br>{justification}</div></div>''', unsafe_allow_html=True)

    st.markdown("### 🤖 AI Scientific Explanation (Stage 3)")
    st.info(result.get("overall_justification", ""))

    st.divider()
    st.markdown("### Feature values & calculation")
    comparison_rows = result.get("feature_comparison", [])
    if comparison_rows:
        rename_map = {
            "feature": "Feature", "earth": "Earth", "target": "Target",
            "absolute_difference": "Absolute difference", "normalized_difference": "Normalized difference",
            "similarity": "Similarity (%)", "weight": "Weight"
        }
        st.dataframe(pd.DataFrame(comparison_rows).rename(columns=rename_map), use_container_width=True, hide_index=True)

    with st.expander("All three condition scores", expanded=True):
        condition_scores = result.get("condition_scores", {})
        if condition_scores:
            score_cols = st.columns(3)
            for i, (condition, value) in enumerate(condition_scores.items()):
                score_cols[i % 3].metric(str(condition), f"{value:.2f}%")

    export_col1, export_col2, lab_col = st.columns(3)
    with export_col1:
        st.download_button("Export JSON", data=json.dumps(result, indent=2, ensure_ascii=False, default=str),
                           file_name="terratwin_analysis_results.json", mime="application/json", use_container_width=True)
    with export_col2:
        if comparison_rows:
            csv_data = pd.DataFrame(comparison_rows).to_csv(index=False).encode("utf-8-sig")
            st.download_button("Export CSV", data=csv_data, file_name="terratwin_feature_comparison.csv",
                               mime="text/csv", use_container_width=True)
    with lab_col:
        st.button("Open Mission Test Lab 🔬 →", type="primary", on_click=go_to, args=("Mission Test Lab",), use_container_width=True)

    st.markdown("### Reference dataset (`terrain_data.csv`)")
    terrain = load_terrain_candidates()
    if terrain is not None and not terrain.empty:
        # نأخذ الكوكب المختار حالياً (Moon أو Mars) ونعرض فقط صفوف Earth + الكوكب المختار
        selected_body = result.get("target_body", st.session_state.mission.get("target_body", "Moon"))
        filtered_terrain = terrain[terrain["body"].isin(["Earth", selected_body])]
        st.caption(f"Showing Earth candidate analogs and {selected_body} reference terrain ({len(filtered_terrain)} records)")
        st.dataframe(filtered_terrain, use_container_width=True, hide_index=True)
    else:
        st.info("Add data/terrain_candidates.csv to display the reference dataset.")

def show_mission_test_lab():
    render_brand_bar()
    render_page_navigation()
    st.title("Mission Test Lab")
    st.caption("Hybrid Terrain Difficulty Classification (75 m Resolution · 16 × 16 km Study Areas)")

    res = st.session_state.get("analysis_result")
    if not isinstance(res, dict) or "mission_lab" not in res:
        res = run_full_analysis()
        st.session_state.analysis_result = res

    lab = res["mission_lab"]
    e_reg = lab["recommended_earth_region"]
    t_reg = lab["target_planetary_region"]
    e_stats = lab["earth_stats"]
    t_stats = lab["target_stats"]

    st.success(f"🎯 **Target Reference:** {t_reg} ({t_stats['body']})  |  🏆 **Recommended Saudi Analog:** {e_reg} (Earth)")

    c1, c2, c3 = st.columns(3)
    c1.metric(f"{e_reg} · Low Difficulty (🟢)", f"{e_stats['low_pct']:.2f}%", f"{e_stats['low_pct'] - t_stats['low_pct']:+.2f}% vs {t_reg}")
    c2.metric(f"{e_reg} · Medium Difficulty (🟡)", f"{e_stats['medium_pct']:.2f}%", f"{e_stats['medium_pct'] - t_stats['medium_pct']:+.2f}% vs {t_reg}")
    c3.metric(f"{e_reg} · High Difficulty (🔴)", f"{e_stats['high_pct']:.2f}%", f"{e_stats['high_pct'] - t_stats['high_pct']:+.2f}% vs {t_reg}")

    st.markdown("### 🤖 AI Terrain Difficulty Explanation (Stage 4)")
    st.info(lab["ai_explanation"])

    st.markdown("### 📊 All 4 Study Regions — Hybrid Classification Breakdown")
    rows = []
    for r_name, r_data in lab["all_regions"].items():
        rows.append({
            "Study Region": r_name,
            "Body": r_data["body"],
            "Low Difficulty 🟢 (%)": r_data["low_pct"],
            "Medium Difficulty 🟡 (%)": r_data["medium_pct"],
            "High Difficulty 🔴 (%)": r_data["high_pct"],
            "Mean Slope (°)": r_data["slope_deg"],
            "Mean Roughness (m)": r_data["roughness_m"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption("Hybrid rules: Low = Slope < 10° AND Roughness < 31.28 m (P65) | High = Slope >= 15° OR Roughness >= 68.30 m (P90) | Medium = Remaining valid pixels.")

def show_about():
    render_brand_bar()
    render_page_navigation()
    st.title("About TerraTwin AI")
    st.markdown("TerraTwin AI · NASA Space Apps Challenge 2026 Prototype")

page = st.session_state.navigation
if page == "Welcome Page":
    show_welcome_page()
elif page == "Mission Control":
    show_mission_control()
elif page == "Mission Configuration":
    show_mission_configuration()
elif page == "Similarity Results":
    show_similarity_results()
elif page == "Mission Test Lab":
    show_mission_test_lab()
elif page == "About TerraTwin":
    show_about()
