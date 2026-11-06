
import streamlit as st
from datetime import datetime
from app import triage

st.set_page_config(
    page_title="PatchPilot | Bug Intelligence",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# SESSION STATE
if "reports" not in st.session_state:
    st.session_state.reports = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "selected_page" not in st.session_state:
    st.session_state.selected_page = "Command Centre"


# NAVIGATION CALLBACK
def go_to_triage():
    st.session_state.selected_page = "New Triage"


# CUSTOM CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(ellipse at top left, #142b49 0%, transparent 45%),
        linear-gradient(135deg, #07111f 0%, #0b1628 55%, #101d31 100%);
    color: #edf4ff;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}

section[data-testid="stSidebar"] {
    background: #081321;
    border-right: 1px solid #1c3450;
}

section[data-testid="stSidebar"] * {
    color: #dce9fa;
}

.hero {
    padding: 34px;
    border-radius: 22px;
    background: linear-gradient(115deg, #102b49, #123d5a, #12304b);
    border: 1px solid #245577;
    box-shadow: 0 15px 45px rgba(0,0,0,0.25);
    animation: appear 0.8s ease-out;
}

.hero h1 {
    font-size: 38px;
    font-weight: 800;
    margin-bottom: 8px;
    color: #ffffff;
}

.hero p {
    color: #b7d2e9;
    font-size: 15px;
}

.eyebrow {
    color: #42d9e8;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 3px;
}

.status {
    display: inline-block;
    padding: 7px 12px;
    border-radius: 20px;
    background: #123e3d;
    color: #67f5d1;
    border: 1px solid #24796c;
    font-size: 11px;
    font-weight: 700;
}

.metric {
    background: linear-gradient(145deg, #142740, #102034);
    border: 1px solid #28415e;
    border-radius: 17px;
    padding: 20px;
    min-height: 125px;
}

.metric-label {
    color: #9bb4cf;
    font-size: 12px;
    font-weight: 600;
}

.metric-value {
    color: #ffffff;
    font-size: 32px;
    font-weight: 800;
    margin-top: 10px;
}

.panel {
    background: #101f33;
    border: 1px solid #263d59;
    border-radius: 17px;
    padding: 22px;
    margin-bottom: 15px;
}

.panel-title {
    color: #ffffff;
    font-size: 17px;
    font-weight: 700;
    margin-bottom: 12px;
}

.muted {
    color: #9bb0c8;
    font-size: 13px;
}

.pulse {
    display: inline-block;
    width: 9px;
    height: 9px;
    background: #48edc1;
    border-radius: 50%;
    margin-right: 8px;
    box-shadow: 0 0 12px #48edc1;
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(72,237,193,0.7); }
    70% { box-shadow: 0 0 0 9px rgba(72,237,193,0); }
    100% { box-shadow: 0 0 0 0 rgba(72,237,193,0); }
}

@keyframes appear {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

div.stButton > button {
    background: linear-gradient(90deg, #087fbd, #13a6b9);
    color: white;
    border: 0;
    border-radius: 10px;
    padding: 10px 18px;
    font-weight: 700;
}

div.stButton > button:hover {
    background: linear-gradient(90deg, #0a9bdc, #21c6d5);
    color: white;
    border: 0;
}

div[data-testid="stForm"] {
    background: #101f33;
    border: 1px solid #263d59;
    padding: 22px;
    border-radius: 17px;
}

.stTextArea textarea, .stTextInput input {
    background: #0b192a !important;
    color: white !important;
    border: 1px solid #34516e !important;
}

h1, h2, h3 {
    color: #f4f8ff;
}

div[data-testid="stMetric"] {
    background: #12243a;
    border: 1px solid #28415e;
    padding: 15px;
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)


# SIDEBAR
with st.sidebar:
    st.markdown("""
    <div style="padding: 12px 0 20px 0;">
        <div style="font-size:30px;">🚀</div>
        <div style="font-size:23px;font-weight:800;color:white;">PatchPilot</div>
        <div style="font-size:10px;letter-spacing:2px;color:#45d9e7;">
            BUG INTELLIGENCE PLATFORM
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<span class="pulse"></span>'
        '<span style="font-size:11px;color:#6cf0cb;font-weight:700;">LOCAL ENGINE READY</span>',
        unsafe_allow_html=True
    )

    st.divider()

    pages = [
        "Command Centre",
        "New Triage",
        "Incident Reports",
        "Analytics",
        "About PatchPilot",
    ]

    page = st.radio(
        "WORKSPACE",
        pages,
        key="selected_page",
        label_visibility="visible",
    )

    st.divider()
    st.markdown("### SYSTEM STATUS")
    st.markdown("🟢 Local engine: Ready")
    st.markdown("🟢 Human approval: Enabled")
    st.markdown("🔵 Mode: Free local prototype")
    st.markdown("🟠 Mattermost: Server reachable; bot not connected")

    st.divider()
    st.caption("PATCHPILOT • HACKATHON PROTOTYPE")


# REUSABLE HERO
def show_hero(title, subtitle):
    st.markdown(f"""
    <div class="hero">
        <div class="eyebrow">PATCHPILOT / BUG INTELLIGENCE</div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
        <span class="status">● SYSTEM OPERATIONAL</span>
    </div>
    """, unsafe_allow_html=True)


# REUSABLE METRIC
def metric_card(label, value, description):
    st.markdown(f"""
    <div class="metric">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="muted">{description}</div>
    </div>
    """, unsafe_allow_html=True)


# COMMAND CENTRE
if page == "Command Centre":
    show_hero(
        "Your Bug Triage Command Centre",
        "A smarter way to understand, prioritize and route software issues."
    )

    st.write("")
    reports = st.session_state.reports

    total = len(reports)
    bugs = sum(r["category"] == "BUG" for r in reports)
    critical = sum(r["priority"] == "CRITICAL" for r in reports)
    pending = sum(r["approval_status"] == "PENDING" for r in reports)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card("TOTAL REPORTS", total, "Reports analyzed")
    with c2:
        metric_card("BUGS DETECTED", bugs, "Classified as bugs")
    with c3:
        metric_card("CRITICAL ISSUES", critical, "Require urgent attention")
    with c4:
        metric_card("PENDING APPROVAL", pending, "Awaiting human review")

    st.write("")
    left, right = st.columns([1.5, 1])

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">⚡ Incident Activity</div>',
                    unsafe_allow_html=True)

        if reports:
            for report in reversed(reports[-5:]):
                st.markdown(
                    f"**{report['category']}** · {report['priority']}"
                )
                st.caption(report["summary"])
                st.divider()
        else:
            st.markdown("### Waiting for your first report")
            st.markdown(
                '<p class="muted">Submit an issue to see PatchPilot analyze it here.</p>',
                unsafe_allow_html=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">🛡️ Safety Controls</div>',
                    unsafe_allow_html=True)
        st.markdown("🟢 Human approval required")
        st.markdown("🟢 No automatic issue assignment")
        st.markdown("🟢 No automatic issue closure")
        st.markdown("🟢 No external changes")
        st.caption("PatchPilot recommends actions. Humans remain in control.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    st.button(
        "＋ Create new triage report",
        type="primary",
        on_click=go_to_triage,
        width="stretch",
    )


# NEW TRIAGE
elif page == "New Triage":
    show_hero(
        "New Issue Triage",
        "Describe an issue and let PatchPilot prepare a structured triage recommendation."
    )

    st.write("")

    with st.form("triage_form"):
        issue = st.text_area(
            "ISSUE DESCRIPTION",
            placeholder=(
                "Example: Users are unable to log in after the latest update. "
                "The login button crashes on macOS."
            ),
            height=180,
        )

        submitted = st.form_submit_button(
            "⚡ Analyze Issue",
            width="stretch",
        )

    if submitted:
        if not issue.strip():
            st.warning("Please enter an issue description first.")
        else:
            with st.spinner("Analyzing issue..."):
                result = triage(issue)

                report = {
                    **result,
                    "created_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
                    "approval_status": "PENDING",
                }

                st.session_state.reports.append(report)
                st.session_state.last_result = report

            st.success("Issue analysis completed.")

    result = st.session_state.last_result

    if result:
        st.divider()
        st.subheader("📋 Triage Recommendation")

        a, b, c = st.columns(3)
        a.metric("CATEGORY", result["category"])
        b.metric("PRIORITY", result["priority"])
        c.metric("AREA", result.get("area", "unknown"))

        st.markdown("### Issue Summary")
        st.write(result["summary"])

        st.markdown("### Why this priority?")
        st.write(result["priority_explanation"])

        if result.get("reasons"):
            st.markdown("### Classification Reasons")
            for reason in result["reasons"]:
                st.write(f"• {reason}")

        st.markdown("### Missing Information")
        missing = result.get("missing_information", [])

        if missing:
            for item in missing:
                st.write(f"• {item}")
        else:
            st.write("No major missing information identified.")

        st.markdown("### Suggested Follow-up Questions")
        questions = result.get("follow_up_questions", [])

        if questions:
            for question in questions:
                st.write(f"• {question}")
        else:
            st.write("No additional questions suggested.")

        st.markdown("### Recommended Team Role")
        st.info(result["suggested_role"])

        st.markdown("### Next Action")
        st.write(result["next_action"])

        st.warning(
            "Human approval required. This is a recommendation only; "
            "PatchPilot has not modified any external system."
        )


# INCIDENT REPORTS
elif page == "Incident Reports":
    show_hero(
        "Incident Reports",
        "Review the issues analyzed during this session."
    )

    reports = st.session_state.reports
    st.write("")

    if not reports:
        st.info("No incident reports yet. Create your first triage report.")
    else:
        for index, report in enumerate(reversed(reports), start=1):
            with st.expander(
                f"{index}. {report['category']} | "
                f"{report['priority']} | {report['created_at']}"
            ):
                st.markdown("**Summary**")
                st.write(report["summary"])
                st.markdown("**Suggested role**")
                st.write(report["suggested_role"])
                st.markdown("**Next action**")
                st.write(report["next_action"])
                st.markdown("**Approval status**")
                st.write(report["approval_status"])


# ANALYTICS
elif page == "Analytics":
    show_hero(
        "Triage Analytics",
        "Understand the reports analyzed in this session."
    )

    reports = st.session_state.reports
    st.write("")

    if not reports:
        st.info("Submit reports to generate analytics.")
    else:
        import pandas as pd

        df = pd.DataFrame(reports)

        st.subheader("Issue Categories")
        st.bar_chart(df["category"].value_counts())

        st.subheader("Priority Distribution")
        st.bar_chart(df["priority"].value_counts())

        st.subheader("Report History")
        st.dataframe(
            df[["created_at", "category", "priority", "area", "suggested_role"]],
            width="stretch",
        )


# ABOUT
elif page == "About PatchPilot":
    show_hero(
        "Meet PatchPilot",
        "A bug-triage teammate designed to help development teams respond to issues."
    )

    st.write("")

    st.markdown("""
    <div class="panel">
        <div class="panel-title">🚀 What PatchPilot Does</div>
        <p class="muted">
        PatchPilot analyzes issue descriptions and prepares structured
        recommendations for software teams.
        </p>
        <ul>
            <li>Classifies reports as BUG, QUESTION or FEATURE REQUEST.</li>
            <li>Suggests a priority and explains the reasoning.</li>
            <li>Identifies missing information.</li>
            <li>Suggests useful follow-up questions.</li>
            <li>Recommends a team role and next action.</li>
        </ul>
    </div>

    <div class="panel">
        <div class="panel-title">🛡️ Human-in-the-Loop Design</div>
        <p class="muted">
        PatchPilot does not automatically assign people, close issues
        or modify external systems. Recommendations require human review.
        </p>
    </div>

    <div class="panel">
        <div class="panel-title">⚙️ Current Prototype</div>
        <p class="muted">
        This version uses a local Python rule-based triage engine.
        It runs without paid APIs or services. Mattermost server is reachable,
        but bot integration is not connected yet.
        </p>
    </div>
    """, unsafe_allow_html=True)
