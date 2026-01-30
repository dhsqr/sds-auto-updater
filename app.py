"""
SDS Auto-Updater - Streamlit Web Dashboard

A vintage-styled dark theme dashboard for monitoring Safety Data Sheets.
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import db, Chemical, SDSVersion, Change
from src.config import SDS_STORAGE_PATH
from src.scheduler import scheduler
from src.health_check import health_checker
from src.backup import backup_manager

# Page configuration
st.set_page_config(
    page_title="SDS Auto-Updater",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Vintage Theme CSS
st.markdown("""
<style>
    /* Import vintage font */
    @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:wght@400;600;700&family=Source+Sans+Pro:wght@400;600&display=swap');
    
    /* Root variables */
    :root {
        --bg-primary: #1a1a1a;
        --bg-secondary: #252525;
        --bg-tertiary: #2d2d2d;
        --text-primary: #e8e4d9;
        --text-secondary: #a69f8f;
        --accent-gold: #c9a227;
        --accent-copper: #b87333;
        --accent-red: #8b3a3a;
        --accent-green: #3a6b3a;
        --border-color: #3d3d3d;
    }
    
    /* Main app background */
    .stApp {
        background: linear-gradient(180deg, #1a1a1a 0%, #0f0f0f 100%);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1f1f1f 0%, #171717 100%);
        border-right: 1px solid #333;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: var(--text-primary);
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Crimson Text', Georgia, serif !important;
        color: var(--text-primary) !important;
        letter-spacing: 0.5px;
    }
    
    h1 {
        border-bottom: 2px solid var(--accent-gold);
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem !important;
    }
    
    /* Body text */
    p, span, div, label {
        font-family: 'Source Sans Pro', sans-serif;
        color: var(--text-secondary);
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-family: 'Crimson Text', Georgia, serif !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: var(--accent-gold) !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-family: 'Source Sans Pro', sans-serif !important;
        color: var(--text-secondary) !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.75rem !important;
    }
    
    [data-testid="stMetricDelta"] {
        color: var(--accent-copper) !important;
    }
    
    /* Cards and containers */
    .stExpander {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 4px !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(180deg, #3d3d3d 0%, #2d2d2d 100%) !important;
        border: 1px solid var(--accent-gold) !important;
        color: var(--text-primary) !important;
        font-family: 'Source Sans Pro', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.8rem !important;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(180deg, var(--accent-gold) 0%, var(--accent-copper) 100%) !important;
        color: #1a1a1a !important;
        border-color: var(--accent-gold) !important;
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        font-family: 'Source Sans Pro', sans-serif !important;
    }
    
    .stSelectbox > div > div {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-color) !important;
    }
    
    /* Data tables */
    .stDataFrame {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
    }
    
    [data-testid="stDataFrame"] {
        background: var(--bg-secondary) !important;
    }
    
    /* Radio buttons in sidebar */
    [data-testid="stSidebar"] .stRadio > label {
        color: var(--text-primary) !important;
    }
    
    /* Dividers */
    hr {
        border-color: var(--border-color) !important;
    }
    
    /* Info/Warning boxes */
    .stAlert {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-secondary) !important;
    }
    
    /* Severity badges */
    .severity-critical {
        background: var(--accent-red);
        color: var(--text-primary);
        padding: 4px 12px;
        border-radius: 2px;
        font-weight: 600;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .severity-important {
        background: var(--accent-copper);
        color: var(--text-primary);
        padding: 4px 12px;
        border-radius: 2px;
        font-weight: 600;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .severity-minor {
        background: var(--accent-green);
        color: var(--text-primary);
        padding: 4px 12px;
        border-radius: 2px;
        font-weight: 600;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Vintage decorative elements */
    .vintage-header {
        background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
        border: 1px solid var(--border-color);
        border-bottom: 3px solid var(--accent-gold);
        padding: 1.5rem 2rem;
        margin-bottom: 2rem;
    }
    
    .vintage-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        background: var(--bg-tertiary) !important;
        border: 1px dashed var(--border-color) !important;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--accent-copper) !important;
        color: var(--accent-copper) !important;
    }
    
    .stDownloadButton > button:hover {
        background: var(--accent-copper) !important;
        color: var(--bg-primary) !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: var(--accent-gold) !important;
    }
    
    /* Code blocks */
    code {
        background: var(--bg-tertiary) !important;
        color: var(--accent-gold) !important;
        border: 1px solid var(--border-color) !important;
    }
    
    /* Dark mode for bar charts */
    [data-testid="stVegaLiteChart"] {
        background: var(--bg-secondary) !important;
        border-radius: 4px;
        padding: 10px;
    }
    
    [data-testid="stVegaLiteChart"] canvas {
        background: var(--bg-secondary) !important;
    }
    
    /* Vega-lite chart background fix */
    .vega-embed {
        background: var(--bg-secondary) !important;
    }
    
    .vega-embed .marks {
        background: var(--bg-secondary) !important;
    }
    
    /* Dark mode for data tables */
    [data-testid="stDataFrame"] > div {
        background: var(--bg-secondary) !important;
    }
    
    [data-testid="stDataFrame"] table {
        background: var(--bg-secondary) !important;
    }
    
    [data-testid="stDataFrame"] th {
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        border-color: var(--border-color) !important;
    }
    
    [data-testid="stDataFrame"] td {
        background: var(--bg-secondary) !important;
        color: var(--text-secondary) !important;
        border-color: var(--border-color) !important;
    }
    
    [data-testid="stDataFrame"] tr:hover td {
        background: var(--bg-tertiary) !important;
    }
    
    /* Dataframe container and glide-data-grid */
    .stDataFrame iframe {
        background: var(--bg-secondary) !important;
    }
    
    div[data-testid="stDataFrame"] > div > div {
        background: var(--bg-secondary) !important;
    }
    
    /* Dark mode for st.code blocks (Previous/Updated comparison) */
    .stCodeBlock, [data-testid="stCodeBlock"] {
        background: var(--bg-tertiary) !important;
    }
    
    .stCodeBlock code, [data-testid="stCodeBlock"] code {
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
    }
    
    .stCodeBlock pre, [data-testid="stCodeBlock"] pre {
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
    }
    
    /* Code block container */
    pre {
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)


def get_severity_indicator(severity: str) -> str:
    """Get text indicator for severity level."""
    indicators = {
        "CRITICAL": "[!]",
        "IMPORTANT": "[*]",
        "MINOR": "[-]"
    }
    return f"{indicators.get(severity, '')} {severity}"


def main():
    # Sidebar navigation
    st.sidebar.markdown("## SDS Auto-Updater")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Chemicals", "Changes", "Upload", "Settings", "System Health"],
        label_visibility="collapsed"
    )
    
    # Quick status in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Quick Status")
    stats = db.get_statistics()

    # Show only critical info in sidebar
    if stats['critical_unresolved'] > 0:
        st.sidebar.error(f"🚨 {stats['critical_unresolved']} Critical Unresolved")

    if stats['unresolved_changes'] > 0:
        st.sidebar.warning(f"⚠️ {stats['unresolved_changes']} Action Required")

    if stats['unresolved_changes'] == 0:
        st.sidebar.success("✅ All Resolved")

    # Last update info
    from datetime import datetime
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    
    # Main content
    if page == "Dashboard":
        show_dashboard()
    elif page == "Chemicals":
        show_chemicals()
    elif page == "Changes":
        show_changes()
    elif page == "Upload":
        show_upload()
    elif page == "Settings":
        show_settings()
    elif page == "System Health":
        show_system_health()


def show_dashboard():
    """Main dashboard view."""
    st.markdown("# Dashboard")
    st.markdown("Real-time Safety Data Sheet monitoring and change detection")

    try:
        stats = db.get_statistics()
    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")
        st.stop()
        return
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="TOTAL CHEMICALS", value=stats['total_chemicals'])
    
    with col2:
        st.metric(label="SDS VERSIONS", value=stats['total_sds_versions'])
    
    with col3:
        st.metric(label="ACTION REQUIRED", value=stats['unresolved_changes'])

    with col4:
        st.metric(label="CRITICAL UNRESOLVED", value=stats['critical_unresolved'])
    
    st.markdown("---")

    # Change Overview Cards (moved to top for better visibility)
    st.markdown("### Change Overview by Severity")

    session = db.get_session()
    try:
        all_changes = session.query(Change).all()
        if all_changes:
            severity_counts = {"CRITICAL": 0, "IMPORTANT": 0, "MINOR": 0}
            for c in all_changes:
                severity_counts[c.severity] = severity_counts.get(c.severity, 0) + 1

            # Display as stat cards
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #8b3a3a 0%, #6d2e2e 100%);
                            padding: 1.5rem; border-radius: 8px; text-align: center;
                            border: 1px solid #5a2424;">
                    <div style="color: #e8e4d9; font-size: 2.5rem; font-weight: 700;
                                font-family: 'Crimson Text', serif;">
                        {severity_counts['CRITICAL']}
                    </div>
                    <div style="color: #a69f8f; font-size: 0.8rem; text-transform: uppercase;
                                letter-spacing: 1px; margin-top: 0.5rem;">
                        🔴 Critical
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #b87333 0%, #8f5a28 100%);
                            padding: 1.5rem; border-radius: 8px; text-align: center;
                            border: 1px solid #704620;">
                    <div style="color: #e8e4d9; font-size: 2.5rem; font-weight: 700;
                                font-family: 'Crimson Text', serif;">
                        {severity_counts['IMPORTANT']}
                    </div>
                    <div style="color: #a69f8f; font-size: 0.8rem; text-transform: uppercase;
                                letter-spacing: 1px; margin-top: 0.5rem;">
                        🟡 Important
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #3a6b3a 0%, #2d5230 100%);
                            padding: 1.5rem; border-radius: 8px; text-align: center;
                            border: 1px solid #244024;">
                    <div style="color: #e8e4d9; font-size: 2.5rem; font-weight: 700;
                                font-family: 'Crimson Text', serif;">
                        {severity_counts['MINOR']}
                    </div>
                    <div style="color: #a69f8f; font-size: 0.8rem; text-transform: uppercase;
                                letter-spacing: 1px; margin-top: 0.5rem;">
                        🟢 Minor
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("*No changes recorded yet*")
    finally:
        session.close()

    st.markdown("---")

    # Two column layout
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Recent Changes")
        
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_changes = db.get_changes_since(week_ago)
        
        if recent_changes:
            session = db.get_session()
            try:
                for change in recent_changes[:10]:
                    chemical = session.query(Chemical).filter(
                        Chemical.id == change.chemical_id
                    ).first()
                    
                    if chemical:
                        severity_class = f"severity-{change.severity.lower()}"
                        if change.is_resolved:
                            status = "✅ Resolved"
                        elif change.is_reviewed:
                            status = "👁️ Reviewed"
                        else:
                            status = "🔔 Pending"
                        
                        st.markdown(f"""
                        <div class="vintage-card">
                            <span class="{severity_class}">{change.severity}</span>
                            <strong style="color: #e8e4d9; margin-left: 10px;">{chemical.chemical_name}</strong>
                            <span style="color: #a69f8f;"> ({chemical.cas_number})</span>
                            <br><br>
                            <span style="color: #a69f8f;">{change.section_changed}: {change.ai_summary or 'Changes detected'}</span>
                            <br>
                            <small style="color: #666;">
                                {change.change_date.strftime('%d %b %Y, %H:%M')} | Status: {status}
                            </small>
                        </div>
                        """, unsafe_allow_html=True)
            finally:
                session.close()
        else:
            st.info("No changes detected in the past 7 days")
    
    with col2:
        st.markdown("### Quick Actions")
        
        if st.button("Run Manual Check", use_container_width=True):
            st.warning("Web scraping requires Chrome browser. This feature checks supplier websites for SDS updates.")
            st.info("For now, you can manually download SDS files and the system will track changes when new versions are uploaded.")
        
        if st.button("Send Weekly Digest", use_container_width=True):
            try:
                from src.alerts.email_alerts import email_service
                if email_service.is_configured():
                    with st.spinner("Sending digest..."):
                        success = email_service.send_weekly_digest()
                    if success:
                        st.success("Digest sent successfully")
                    else:
                        st.error("Failed to send digest")
                else:
                    st.warning("Email not configured. Add Gmail credentials to .env file.")
            except Exception as e:
                st.error(f"Email service error: {str(e)[:100]}")
        
        st.markdown("---")
        st.markdown("### Activity Timeline")

        # Timeline chart (changes over time)
        session = db.get_session()
        try:
            all_changes = session.query(Change).all()
            if all_changes and len(all_changes) > 1:
                # Prepare timeline data
                timeline_data = []
                for change in all_changes:
                    timeline_data.append({
                        'Date': change.change_date.strftime('%Y-%m-%d'),
                        'Severity': change.severity,
                        'Count': 1
                    })

                df_timeline = pd.DataFrame(timeline_data)
                df_timeline = df_timeline.groupby(['Date', 'Severity']).count().reset_index()

                import altair as alt

                # Color mapping
                color_scale = alt.Scale(
                    domain=['CRITICAL', 'IMPORTANT', 'MINOR'],
                    range=['#8b3a3a', '#b87333', '#3a6b3a']
                )

                # Area chart for timeline
                timeline_chart = alt.Chart(df_timeline).mark_area(
                    opacity=0.7,
                    interpolate='monotone'
                ).encode(
                    x=alt.X('Date:T', axis=alt.Axis(
                        labelColor='#a69f8f',
                        titleColor='#e8e4d9',
                        title='Date'
                    )),
                    y=alt.Y('Count:Q', axis=alt.Axis(
                        labelColor='#a69f8f',
                        titleColor='#e8e4d9',
                        title='Changes'
                    ), stack='zero'),
                    color=alt.Color('Severity:N', scale=color_scale, legend=alt.Legend(
                        labelColor='#e8e4d9',
                        titleColor='#e8e4d9'
                    )),
                    tooltip=['Date:T', 'Severity:N', 'Count:Q']
                ).configure(
                    background='#252525'
                ).configure_axis(
                    gridColor='#3d3d3d',
                    domainColor='#3d3d3d'
                ).configure_view(
                    strokeWidth=0
                ).properties(
                    height=200
                )

                st.altair_chart(timeline_chart, use_container_width=True)
            elif all_changes and len(all_changes) == 1:
                st.info("*Only one change recorded - timeline needs more data*")
            else:
                st.info("*No changes recorded yet*")
        finally:
            session.close()


def show_chemicals():
    """Chemicals inventory view."""
    st.markdown("# Chemical Inventory")
    
    # Search
    search = st.text_input("Search by name or CAS number", placeholder="Enter chemical name or CAS...")
    
    # Get all chemicals
    session = db.get_session()
    try:
        query = session.query(Chemical).filter(Chemical.is_active == 1)
        
        if search:
            query = query.filter(
                (Chemical.chemical_name.contains(search)) |
                (Chemical.cas_number.contains(search))
            )
        
        chemicals = query.all()
        
        if chemicals:
            # Create dataframe
            data = []
            for chem in chemicals:
                latest_sds = db.get_latest_sds_version(chem.id)
                data.append({
                    "Chemical Name": chem.chemical_name,
                    "CAS Number": chem.cas_number,
                    "Supplier": chem.supplier,
                    "Last Checked": chem.last_checked.strftime("%Y-%m-%d %H:%M") if chem.last_checked else "Never",
                    "Last Updated": chem.last_updated.strftime("%Y-%m-%d") if chem.last_updated else "N/A",
                    "SDS Available": "Yes" if latest_sds else "No"
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.markdown(f"*Showing {len(chemicals)} chemicals*")
            
            # Download option
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name="chemicals_inventory.csv",
                mime="text/csv"
            )
        else:
            st.warning("No chemicals found. Use the Upload page to add chemicals.")
    finally:
        session.close()


def show_changes():
    """Changes history view."""
    st.markdown("# Change History")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        severity_filter = st.selectbox(
            "Severity",
            ["All", "CRITICAL", "IMPORTANT", "MINOR"]
        )
    
    with col2:
        status_filter = st.selectbox(
            "Status",
            ["All", "Unresolved", "Resolved", "Pending Review", "Reviewed"]
        )
    
    with col3:
        date_filter = st.selectbox(
            "Time Period",
            ["Last 7 days", "Last 30 days", "All time"]
        )
    
    st.markdown("---")
    
    # Get changes with filters
    session = db.get_session()
    try:
        query = session.query(Change)
        
        if severity_filter != "All":
            query = query.filter(Change.severity == severity_filter)
        
        if status_filter == "Unresolved":
            query = query.filter(Change.is_resolved == 0)
        elif status_filter == "Resolved":
            query = query.filter(Change.is_resolved == 1)
        elif status_filter == "Pending Review":
            query = query.filter(Change.is_reviewed == 0)
        elif status_filter == "Reviewed":
            query = query.filter(Change.is_reviewed == 1)
        
        if date_filter == "Last 7 days":
            query = query.filter(Change.change_date >= datetime.utcnow() - timedelta(days=7))
        elif date_filter == "Last 30 days":
            query = query.filter(Change.change_date >= datetime.utcnow() - timedelta(days=30))
        
        changes = query.order_by(Change.change_date.desc()).all()
        
        if changes:
            for change in changes:
                chemical = session.query(Chemical).filter(
                    Chemical.id == change.chemical_id
                ).first()
                
                if chemical:
                    # Add status badge to expander title
                    status_badge = ""
                    if change.is_resolved:
                        status_badge = " ✅ RESOLVED"
                    elif change.is_reviewed:
                        status_badge = " 👁️ REVIEWED"
                    else:
                        status_badge = " 🔔 NEW"

                    with st.expander(
                        f"[{change.severity}] {chemical.chemical_name} - {change.section_changed}{status_badge}"
                    ):
                        st.markdown(f"**CAS Number:** {chemical.cas_number}")
                        st.markdown(f"**Date:** {change.change_date.strftime('%d %B %Y at %H:%M')}")
                        st.markdown(f"**Severity:** {change.severity}")
                        st.markdown(f"**Summary:** {change.ai_summary or 'No summary available'}")

                        # Show resolution status
                        st.markdown("---")
                        col_status1, col_status2 = st.columns(2)
                        with col_status1:
                            if change.is_resolved:
                                st.success(f"✅ Resolved by {change.resolved_by}")
                                st.caption(f"Resolved on: {change.resolved_at.strftime('%d %b %Y, %H:%M')}")
                                if change.resolution_notes:
                                    st.info(f"**Resolution Notes:** {change.resolution_notes}")
                            else:
                                st.warning("⚠️ Not Resolved Yet")

                        with col_status2:
                            if change.is_reviewed:
                                st.info(f"👁️ Reviewed by {change.reviewed_by}")
                                st.caption(f"Reviewed on: {change.reviewed_at.strftime('%d %b %Y, %H:%M')}")
                            else:
                                st.warning("🔔 Pending Review")

                        st.markdown("---")

                        if change.old_value and change.new_value:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**Previous:**")
                                st.code(change.old_value[:500])
                            with col2:
                                st.markdown("**Updated:**")
                                st.code(change.new_value[:500])

                        st.markdown("---")

                        # Action buttons
                        if not change.is_resolved:
                            st.markdown("### 🎯 Take Action")

                            col_btn1, col_btn2 = st.columns(2)

                            with col_btn1:
                                if not change.is_reviewed:
                                    if st.button("👁️ Mark as Reviewed", key=f"review_{change.id}", use_container_width=True):
                                        db.mark_change_reviewed(change.id, "Dashboard User")
                                        st.success("Marked as reviewed")
                                        st.rerun()

                            with col_btn2:
                                if st.button("✅ Mark as Resolved", key=f"resolve_btn_{change.id}", use_container_width=True, type="primary"):
                                    st.session_state[f"show_resolve_form_{change.id}"] = True
                                    st.rerun()

                            # Show resolution form if button clicked
                            if st.session_state.get(f"show_resolve_form_{change.id}", False):
                                st.markdown("#### Resolution Details")

                                resolution_notes = st.text_area(
                                    "What action did you take to resolve this?",
                                    placeholder="Example: Updated SOP document, trained staff on new PPE requirements, updated inventory labels, etc.",
                                    key=f"notes_{change.id}",
                                    height=100
                                )

                                col_submit, col_cancel = st.columns(2)

                                with col_submit:
                                    if st.button("✅ Confirm Resolution", key=f"confirm_{change.id}", use_container_width=True):
                                        if resolution_notes.strip():
                                            db.mark_change_resolved(change.id, "Dashboard User", resolution_notes)
                                            st.success("✅ Change marked as resolved!")
                                            st.session_state[f"show_resolve_form_{change.id}"] = False
                                            st.rerun()
                                        else:
                                            st.error("Please add resolution notes")

                                with col_cancel:
                                    if st.button("Cancel", key=f"cancel_{change.id}", use_container_width=True):
                                        st.session_state[f"show_resolve_form_{change.id}"] = False
                                        st.rerun()
                        else:
                            st.success("✅ This change has been resolved. No further action needed.")
        else:
            st.info("No changes found matching your filters")
    finally:
        session.close()


def show_upload():
    """Upload chemicals view."""
    st.markdown("# Upload Chemicals")
    
    st.markdown("""
    Upload a CSV file with your chemical inventory. The file should have these columns:
    
    - **chemical_name** (required)
    - **cas_number** (required)  
    - **supplier** (required) - one of: `sigma_aldrich`, `merck`, `srl_chemicals`
    - **product_id** (optional) - supplier's product code
    """)
    
    # Sample template with 10 chemicals
    sample_csv = """chemical_name,cas_number,supplier,product_id
Sodium Hydroxide,1310-73-2,sigma_aldrich,S5881
Hydrochloric Acid,7647-01-0,sigma_aldrich,H1758
Sulfuric Acid,7664-93-9,sigma_aldrich,258105
Acetone,67-64-1,sigma_aldrich,270725
Methanol,67-56-1,sigma_aldrich,322415
Ethanol,64-17-5,sigma_aldrich,459844
Potassium Permanganate,7722-64-7,srl_chemicals,89541
Copper Sulfate,7758-99-8,merck,102790
Phenolphthalein,77-09-8,srl_chemicals,89493
Nitric Acid,7697-37-2,sigma_aldrich,438073"""
    
    st.download_button(
        label="Download Sample Template",
        data=sample_csv,
        file_name="chemicals_template.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    
    # File upload
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)

            st.markdown("### Preview")
            st.dataframe(df.head(10), use_container_width=True, hide_index=True)

            # Validate columns
            required_cols = ['chemical_name', 'cas_number', 'supplier']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                st.error(f"Missing required columns: {', '.join(missing_cols)}")
            else:
                # Check for empty required fields
                empty_rows = df[required_cols].isnull().any(axis=1).sum()
                if empty_rows > 0:
                    st.warning(f"⚠️ {empty_rows} rows have empty required fields and will be skipped")

                st.success(f"✅ Found {len(df) - empty_rows} valid chemicals to import")

                if st.button("Import Chemicals", type="primary"):
                    try:
                        # Save temp file and import
                        temp_path = Path("data") / "temp_upload.csv"
                        temp_path.parent.mkdir(parents=True, exist_ok=True)
                        df.to_csv(temp_path, index=False)

                        with st.spinner("Importing chemicals..."):
                            count = db.import_chemicals_from_csv(str(temp_path))

                        temp_path.unlink()  # Clean up

                        if count > 0:
                            st.success(f"✅ Successfully imported {count} new chemicals")
                            st.balloons()
                        else:
                            st.info("No new chemicals imported (all may already exist in database)")

                    except ValueError as ve:
                        st.error(f"Validation error: {str(ve)}")
                    except Exception as e:
                        st.error(f"Import error: {str(e)}")

        except pd.errors.EmptyDataError:
            st.error("The uploaded file is empty")
        except pd.errors.ParserError:
            st.error("Error parsing CSV file. Please check the file format")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")


def show_settings():
    """Settings view."""
    st.markdown("# Settings")
    
    st.markdown("### Email Configuration")
    
    from src.config import GMAIL_SENDER_EMAIL, ALERT_RECIPIENTS
    
    if GMAIL_SENDER_EMAIL:
        st.markdown(f"**Sender Email:** `{GMAIL_SENDER_EMAIL}`")
    else:
        st.warning("Sender email not configured")
    
    if ALERT_RECIPIENTS:
        st.markdown(f"**Recipients:** `{', '.join(ALERT_RECIPIENTS)}`")
    else:
        st.warning("No recipients configured")
    
    st.info("Email settings are configured in the `.env` file")
    
    # Test email
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Send Test Email"):
            from src.alerts.email_alerts import email_service
            if email_service.is_configured():
                with st.spinner("Sending test email..."):
                    success = email_service.send_test_email()
                if success:
                    st.success("Test email sent")
                else:
                    st.error("Failed to send test email")
            else:
                st.error("Email not configured. Check your .env file.")
    
    st.markdown("---")
    
    st.markdown("### System Configuration")
    
    from src.config import DAILY_CHECK_HOUR, WEEKLY_DIGEST_DAY
    
    st.markdown(f"**Daily Check Time:** {DAILY_CHECK_HOUR}:00")
    st.markdown(f"**Weekly Digest Day:** {WEEKLY_DIGEST_DAY}")
    
    st.markdown("---")
    
    st.markdown("### Database Statistics")
    
    stats = db.get_statistics()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"- Total Chemicals: **{stats['total_chemicals']}**")
        st.markdown(f"- SDS Versions: **{stats['total_sds_versions']}**")
        st.markdown(f"- Total Changes: **{stats['total_changes']}**")
    with col2:
        st.markdown(f"- Unreviewed: **{stats['unreviewed_changes']}**")
        st.markdown(f"- Critical: **{stats['critical_changes']}**")
    
    st.markdown("---")
    
    st.markdown("### Danger Zone")

    with st.expander("Reset Database"):
        st.warning("This will delete all data including chemicals, SDS versions, and changes.")
        st.markdown("To reset, delete the database file manually: `data/sds_database.db`")


def show_system_health():
    """System health and monitoring view."""
    st.markdown("# System Health")

    # Run health check button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # Run health check
    with st.spinner("Running health check..."):
        health_results = health_checker.run_full_health_check()

    # Overall status
    status_colors = {
        'healthy': '🟢',
        'degraded': '🟡',
        'unhealthy': '🔴'
    }

    st.markdown(f"## {status_colors.get(health_results['overall_status'], '⚪')} Overall Status: {health_results['overall_status'].upper()}")

    # Create columns for different health checks
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📁 Database")
        db_health = health_results['database']
        if db_health['status'] == 'healthy':
            st.success("Database is healthy")
            stats = db_health['statistics']
            st.markdown(f"- **Chemicals:** {stats['total_chemicals']}")
            st.markdown(f"- **SDS Versions:** {stats['total_sds_versions']}")
            st.markdown(f"- **Changes:** {stats['total_changes']}")
            st.markdown(f"- **Size:** {db_health.get('size', 0) / 1024 / 1024:.2f} MB")
        else:
            st.error(f"Database issue: {db_health.get('message', 'Unknown error')}")

        st.markdown("### 🔑 API Configuration")
        api_health = health_results['api_configuration']
        if api_health['status'] == 'healthy':
            st.success("All required APIs configured")
        elif api_health['status'] == 'degraded':
            st.warning("Some optional APIs not configured")
        else:
            st.error("Required APIs missing")

        for api_name, api_info in api_health['checks'].items():
            if api_info['configured']:
                st.markdown(f"✅ **{api_name.upper()}**: Configured")
            elif api_info['required']:
                st.markdown(f"❌ **{api_name.upper()}**: Missing (Required)")
            else:
                st.markdown(f"⚠️ **{api_name.upper()}**: Not configured (Optional)")

    with col2:
        st.markdown("### 💾 Storage")
        storage_health = health_results['storage']
        if storage_health['status'] == 'healthy':
            st.success("Storage is healthy")
            st.markdown(f"- **PDF Files:** {storage_health['pdf_count']}")
            st.markdown(f"- **Total Size:** {storage_health['total_size_mb']} MB")
            st.markdown(f"- **Disk Free:** {storage_health['disk_free_gb']} GB")
            st.markdown(f"- **Disk Usage:** {storage_health['disk_percent_used']}%")
        else:
            st.error(f"Storage issue: {storage_health.get('message', 'Unknown error')}")

        st.markdown("### 💻 System Resources")
        sys_health = health_results['system_resources']
        if sys_health['status'] == 'healthy':
            st.success("System resources normal")
            st.markdown(f"- **CPU Usage:** {sys_health['cpu_percent']}%")
            st.markdown(f"- **Memory Usage:** {sys_health['memory_percent']}%")
            st.markdown(f"- **Available RAM:** {sys_health['memory_available_gb']} GB")
        else:
            st.error(f"System issue: {sys_health.get('message', 'Unknown error')}")

    st.markdown("---")

    # Database Backups Section
    st.markdown("## 💾 Database Backups")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Create Backup", use_container_width=True):
            with st.spinner("Creating backup..."):
                backup_path = backup_manager.create_backup()
            if backup_path:
                st.success(f"Backup created: {backup_path.name}")
            else:
                st.error("Failed to create backup")

    with col2:
        if st.button("Auto Backup Check", use_container_width=True):
            with st.spinner("Checking..."):
                result = backup_manager.auto_backup_if_needed(days_threshold=7)
            if result:
                st.success(f"Auto backup created: {result.name}")
            else:
                st.info("Recent backup exists, no action needed")

    st.markdown("### Available Backups")
    backups = backup_manager.list_backups()

    if backups:
        backup_data = []
        for backup in backups:
            backup_data.append({
                "Filename": backup['filename'],
                "Created": backup['created_str'],
                "Size (MB)": backup['size_mb']
            })

        df = pd.DataFrame(backup_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No backups found")

    st.markdown("---")

    # System Information
    st.markdown("## ℹ️ System Information")
    uptime_info = health_checker.get_uptime_info()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Check Time:** {health_results['timestamp']}")
    with col2:
        if 'uptime_hours' in uptime_info:
            st.markdown(f"**System Uptime:** {uptime_info['uptime_hours']:.1f} hours")


if __name__ == "__main__":
    main()
