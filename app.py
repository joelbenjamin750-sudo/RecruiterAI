import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from database import SessionLocal, init_db
from models import Candidate, Job, Offer, Application
import os
import tempfile
from document_parser import extract_text
from ai_engine import analyze_candidate
import analytics_service
import risk_service
import followup_service

# Initial Setup
st.set_page_config(
    page_title="RecruiterAI | Risk & Engagement Platform",
    page_icon="🚀",
    layout="wide"
)

# Initialize Database Tables
try:
    init_db()
except Exception as e:
    st.error(f"Database initialization failed: {e}")
    st.stop()

# --- SESSION STATE MANAGEMENT ---
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

def navigate_to(page):
    st.session_state.current_page = page

# --- DATABASE HELPERS ---
def get_db():
    return SessionLocal()

# --- UI COMPONENTS ---

def render_dashboard():
    st.header("📊 Recruiter Dashboard")

    db = get_db()
    try:
        total_candidates = db.query(Candidate).count()
        total_jobs = db.query(Job).count()
        total_offers = db.query(Offer).count()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Candidates", total_candidates)
        col2.metric("Open Jobs", total_jobs)
        col3.metric("Offers Released", total_offers)

        st.divider()
        st.subheader("Quick Actions")
        c1, c2, c3 = st.columns(3)
        if c1.button("➕ Add Candidate"): navigate_to("Candidates")
        if c2.button("💼 Create Job"): navigate_to("Jobs")
        if c3.button("📜 Release Offer"): navigate_to("Offers")

    finally:
        db.close()

def render_candidates():
    st.header("👥 Candidate Management")

    tab1, tab2 = st.tabs(["View Candidates", "Add New Candidate"])

    with tab1:
        db = get_db()
        try:
            candidates = db.query(Candidate).all()
            if candidates:
                df = pd.DataFrame([
                    {
                        "ID": c.candidate_id,
                        "Name": c.name,
                        "Email": c.email,
                        "Experience": c.total_experience,
                        "Current Co": c.current_company,
                        "CTC": c.current_ctc
                    } for c in candidates
                ])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No candidates found in database.")
        finally:
            db.close()

    with tab2:
        with st.form("add_candidate"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name*")
                email = st.text_input("Email*")
                phone = st.text_input("Phone")
                current_company = st.text_input("Current Company")
                current_designation = st.text_input("Current Designation")
            with col2:
                total_exp = st.number_input("Total Experience (Years)", min_value=0.0, step=0.1)
                skills = st.text_area("Skills (comma separated)")
                current_ctc = st.number_input("Current CTC", min_value=0.0)
                expected_ctc = st.number_input("Expected CTC", min_value=0.0)
                notice_period = st.number_input("Notice Period (Days)", min_value=0, step=1)

            col3, col4 = st.columns(2)
            with col3:
                location = st.text_input("Current Location")
                preferred_location = st.text_input("Preferred Location")
            with col4:
                work_mode = st.selectbox("Preferred Work Mode", ["Remote", "Hybrid", "Onsite"])
                reason_for_change = st.text_area("Reason for Change")

            submit = st.form_submit_button("Save Candidate")

            if submit:
                if not name or not email:
                    st.error("Name and Email are required.")
                else:
                    db = get_db()
                    try:
                        new_candidate = Candidate(
                            name=name, email=email, phone=phone,
                            current_company=current_company, current_designation=current_designation,
                            total_experience=total_exp, skills=skills,
                            current_ctc=current_ctc, expected_ctc=expected_ctc,
                            notice_period=notice_period, location=location,
                            preferred_location=preferred_location, work_mode=work_mode,
                            reason_for_change=reason_for_change
                        )
                        db.add(new_candidate)
                        db.commit()
                        st.success(f"Candidate {name} saved successfully!")
                    except Exception as e:
                        st.error(f"Error saving candidate: {e}")
                    finally:
                        db.close()

def render_jobs():
    st.header("💼 Job Management")

    tab1, tab2 = st.tabs(["View Jobs", "Create Job"])

    with tab1:
        db = get_db()
        try:
            jobs = db.query(Job).all()
            if jobs:
                df = pd.DataFrame([
                    {
                        "ID": j.job_id,
                        "Client": j.client,
                        "Title": j.job_title,
                        "Tech": j.technology,
                        "Location": j.location,
                        "Budget Max": j.salary_max
                    } for j in jobs
                ])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No jobs found.")
        finally:
            db.close()

    with tab2:
        with st.form("add_job"):
            col1, col2 = st.columns(2)
            with col1:
                client = st.text_input("Client Name*")
                job_title = st.text_input("Job Title*")
                technology = st.text_input("Primary Technology")
                location = st.text_input("Location")
                work_mode = st.selectbox("Work Mode", ["Remote", "Hybrid", "Onsite"])
            with col2:
                exp_min = st.number_input("Min Experience", min_value=0.0)
                exp_max = st.number_input("Max Experience", min_value=0.0)
                salary_min = st.number_input("Min Salary", min_value=0.0)
                salary_max = st.number_input("Max Salary", min_value=0.0)
                notice_req = st.text_input("Notice Period Requirement")

            submit = st.form_submit_button("Create Job")
            if submit:
                if not client or not job_title:
                    st.error("Client and Job Title are required.")
                else:
                    db = get_db()
                    try:
                        new_job = Job(
                            client=client, job_title=job_title, technology=technology,
                            location=location, work_mode=work_mode,
                            experience_min=exp_min, experience_max=exp_max,
                            salary_min=salary_min, salary_max=salary_max,
                            notice_requirement=notice_req
                        )
                        db.add(new_job)
                        db.commit()
                        st.success("Job created successfully!")
                    except Exception as e:
                        st.error(f"Error creating job: {e}")
                    finally:
                        db.close()

def render_offers():
    st.header("📜 Offer Management")

    tab1, tab2 = st.tabs(["View Offers", "Release New Offer"])

    with tab1:
        db = get_db()
        try:
            offers = db.query(Offer).all()
            if offers:
                df = pd.DataFrame([
                    {
                        "ID": o.offer_id,
                        "Candidate ID": o.candidate_id,
                        "Job ID": o.job_id,
                        "Joining Date": o.joining_date,
                        "CTC": o.offered_ctc,
                        "Status": o.candidate_status
                    } for o in offers
                ])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No offers released yet.")
        finally:
            db.close()

    with tab2:
        with st.form("add_offer"):
            col1, col2 = st.columns(2)
            with col1:
                cand_id = st.number_input("Candidate ID", min_value=1, step=1)
                job_id = st.number_input("Job ID", min_value=1, step=1)
                offer_date = st.date_input("Offer Date", value=date.today())
                joining_date = st.date_input("Expected Joining Date")
            with col2:
                offered_ctc = st.number_input("Offered CTC", min_value=0.0)
                fixed_ctc = st.number_input("Fixed CTC", min_value=0.0)
                variable_ctc = st.number_input("Variable CTC", min_value=0.0)
                cand_status = st.selectbox("Initial Status", ["Pending", "Accepted", "Declined"])

            submit = st.form_submit_button("Release Offer")
            if submit:
                db = get_db()
                try:
                    new_offer = Offer(
                        candidate_id=cand_id, job_id=job_id,
                        offer_date=offer_date, joining_date=joining_date,
                        offered_ctc=offered_ctc, fixed_ctc=fixed_ctc,
                        variable_ctc=variable_ctc, candidate_status=cand_status
                    )
                    db.add(new_offer)
                    db.commit()

                    # Automatically calculate risk score upon offer release
                    risk_service.RiskCalculationEngine.calculate_risk(db, cand_id, new_offer.offer_id)

                    st.success("Offer recorded and risk analyzed successfully!")
                except Exception as e:
                    st.error(f"Error releasing offer: {e}")
                finally:
                    db.close()

def render_resume_screening():
    st.header("🔍 Resume Screening (Original Tool)")

    st.caption("AI-powered CV & JD screening assistant")
    st.divider()

    jd_text = st.text_area("Paste the Job Description", height=200, placeholder="Paste the complete JD here...")
    cv_files = st.file_uploader("Upload Candidate CV(s)", type=["pdf", "docx"], accept_multiple_files=True)

    if st.button("Analyze Candidate(s)", type="primary", use_container_width=True):
        if not jd_text:
            st.warning("⚠️ Please paste the Job Description.")
        elif not cv_files:
            st.warning("⚠️ Please upload at least one CV.")
        else:
            for cv in cv_files:
                st.subheader(f"👤 {cv.name}")
                suffix = os.path.splitext(cv.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                    temp_file.write(cv.getbuffer())
                    temp_path = temp_file.name
                try:
                    with st.spinner(f"AI is analyzing {cv.name}..."):
                        resume_text = extract_text(temp_path)
                        result = analyze_candidate(jd_text, resume_text)
                    st.markdown(result)
                except Exception as e:
                    st.error(f"Error analyzing {cv.name}: {e}")
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

def render_risk_monitor():
    st.header("⚠️ Risk Monitoring System")
    st.caption("Identify and mitigate risks for candidates in the offer stage")
    st.divider()

    db = get_db()
    try:
        # 1. High-Risk Alert Panel
        high_risk_candidates = risk_service.get_high_risk_candidates(db)
        if high_risk_candidates:
            st.subheader("🚨 High Risk Alerts")
            for risk in high_risk_candidates:
                cand = db.query(Candidate).filter(Candidate.candidate_id == risk.candidate_id).first()
                name = cand.name if cand else "Unknown"

                with st.expander(f"CRITICAL RISK: {name} (Score: {risk.risk_score})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Recommended Action:** {risk.recommended_action}")
                        st.markdown(f"**Risk Level:** {risk.risk_level}")
                    with col2:
                        st.write(f"Counter-offer Risk: {risk.counteroffer_risk}")
                        st.write(f"Competing Offer Risk: {risk.competing_offer_risk}")
                        st.write(f"Notice Period Risk: {risk.notice_period_risk}")
                        st.write(f"Comp Gap Risk: {risk.compensation_risk}")
        else:
            st.success("No high-risk candidates detected! ✅")

        st.divider()

        # 2. Full Risk Table
        st.subheader("All Candidate Risk Scores")
        all_risks = db.query(risk_service.RiskScore).all()
        if all_risks:
            risk_data = []
            for r in all_risks:
                cand = db.query(Candidate).filter(Candidate.candidate_id == r.candidate_id).first()
                risk_data.append({
                    "Candidate": cand.name if cand else "Unknown",
                    "Score": r.risk_score,
                    "Level": r.risk_level,
                    "Action": r.recommended_action
                })
            st.table(pd.DataFrame(risk_data))
        else:
            st.info("No risk data available. Please release offers to trigger analysis.")

    finally:
        db.close()

def render_analytics():
    st.header("📈 Recruitment Analytics")
    st.caption("Data-driven insights into your hiring pipeline and candidate risk")
    st.divider()

    db = get_db()
    try:
        # 1. High-Level KPIs
        kpis = analytics_service.get_high_level_kpis(db)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Overall Conv. Rate", f"{kpis['conversion_rate']:.1f}%")
        col2.metric("Offer Acceptance", f"{kpis['offer_acceptance_rate']:.1f}%")
        col3.metric("High Risk Candidates", kpis['high_risk_count'])
        col4.metric("Total Pipeline", kpis['total_pipeline'])

        st.divider()

        # 2. Visualizations
        row1_col1, row1_col2 = st.columns([2, 1])

        with row1_col1:
            st.subheader("Pipeline Funnel")
            df_funnel = analytics_service.get_pipeline_stats(db)
            if not df_funnel.empty:
                # Define standard funnel order
                funnel_order = ["Applied", "Screening", "Interview", "Offered", "Joined"]
                df_funnel['Status'] = pd.Categorical(df_funnel['Status'], categories=funnel_order, ordered=True)
                df_funnel = df_funnel.sort_values('Status')

                fig_funnel = px.funnel(df_funnel, x='Count', y='Status',
                                     title="Candidate Flow",
                                     color_discrete_sequence=['#636EFA'])
                st.plotly_chart(fig_funnel, use_container_width=True)
            else:
                st.info("No pipeline data available.")

        with row1_col2:
            st.subheader("Offer Outcomes")
            df_offers = analytics_service.get_offer_conversion_stats(db)
            if not df_offers.empty:
                fig_pie = px.pie(df_offers, values='Count', names='Status',
                               title="Offer Status Distribution",
                               hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No offer data available.")

        st.divider()

        row2_col1, row2_col2 = st.columns(2)

        with row2_col1:
            st.subheader("Risk Distribution")
            df_risk = analytics_service.get_risk_distribution(db)
            if not df_risk.empty:
                fig_risk = px.bar(df_risk, x='Risk Level', y='Count',
                                 title="Candidate Risk Levels",
                                 color='Risk Level',
                                 color_discrete_map={'LOW': 'green', 'MEDIUM': 'orange', 'HIGH': 'red'})
                st.plotly_chart(fig_risk, use_container_width=True)
            else:
                st.info("No risk data available.")

        with row2_col2:
            st.subheader("Source Effectiveness")
            df_source = analytics_service.get_source_effectiveness(db)
            if not df_source.empty:
                fig_source = px.bar(df_source, x='Count', y='Source',
                                   title="Hires by Source",
                                   orientation='h',
                                   color_discrete_sequence=['#AB63FA'])
                st.plotly_chart(fig_source, use_container_width=True)
                # Sort by count for better visibility
                df_source = df_source.sort_values('Count', ascending=False)
            else:
                st.info("No source data available.")

        st.divider()

        st.subheader("Compensation Analysis")
        df_comp = analytics_service.get_compensation_stats(db)
        if not df_comp.empty:
            fig_comp = px.scatter(df_comp, x='Expected CTC', y='Offered CTC',
                                 title="Expected vs Offered Compensation",
                                 labels={'Expected CTC': 'Expected (Annual)', 'Offered CTC': 'Offered (Annual)'},
                                 trendline="ols")
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("No compensation data available.")

    finally:
        db.close()

def render_followups():
    st.header("📅 Follow-up Management")
    st.caption("Ensure active engagement with candidates to maximize offer acceptance")
    st.divider()

    db = get_db()
    try:
        tab1, tab2, tab3 = st.tabs(["Today's Agenda", "Pending Actions", "Schedule New"])

        with tab1:
            st.subheader("Today's Tasks")
            agenda = followup_service.FollowupService.get_todays_agenda(db)
            if agenda:
                for f in agenda:
                    # Join with candidate for name
                    cand = db.query(Candidate).filter(Candidate.candidate_id == f.candidate_id).first()
                    name = cand.name if cand else "Unknown"

                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.markdown(f"**{name}**\n\n{f.message}")

                    if col2.button("Mark Sent", key=f"sent_{f.followup_id}"):
                        followup_service.FollowupService.complete_followup(db, f.followup_id, "Sent")
                        st.rerun()

                    if col3.button("Mark Responded", key=f"resp_{f.followup_id}"):
                        # In a real app we'd use a modal; for simplicity we mark as responded
                        followup_service.FollowupService.complete_followup(db, f.followup_id, "Responded", "Candidate responded via channel.")
                        st.rerun()
            else:
                st.success("No follow-ups scheduled for today! ✅")

        with tab2:
            st.subheader("Pending & Suggested Actions")

            # Overdue
            st.markdown("#### ⏳ Overdue Follow-ups")
            overdue = followup_service.FollowupService.get_overdue_followups(db)
            if overdue:
                for f in overdue:
                    cand = db.query(Candidate).filter(Candidate.candidate_id == f.candidate_id).first()
                    name = cand.name if cand else "Unknown"
                    st.warning(f"Overdue: {name} - {f.message}")
                    if st.button(f"Reschedule {name}", key=f"resched_{f.followup_id}"):
                        from datetime import datetime, timedelta
                        followup_service.FollowupService.schedule_followup(
                            db, f.candidate_id, f.offer_id,
                            datetime.now().date() + timedelta(days=1),
                            f.channel, f.message
                        )
                        followup_service.FollowupService.complete_followup(db, f.followup_id, "Sent")
                        st.rerun()
            else:
                st.info("No overdue follow-ups.")

            st.divider()

            # AI Suggestions
            st.markdown("#### 🤖 AI Suggestions")
            suggestions = followup_service.FollowupService.get_followup_suggestions(db)
            if suggestions:
                for s in suggestions:
                    cand = db.query(Candidate).filter(Candidate.candidate_id == s['candidate_id']).first()
                    name = cand.name if cand else "Unknown"

                    col1, col2 = st.columns([3, 1])
                    col1.markdown(f"**{name}** - {s['reason']} ({s['priority']} Priority)")
                    if col2.button("Schedule Follow-up", key=f"sug_{s['candidate_id']}"):
                        followup_service.FollowupService.schedule_followup(
                            db, s['candidate_id'], s['offer_id'],
                            datetime.now().date(),
                            "Phone", "Checking in on the offer status."
                        )
                        st.success(f"Follow-up scheduled for {name}!")
                        st.rerun()
            else:
                st.info("No new suggestions at this time.")

        with tab3:
            st.subheader("Schedule Manual Follow-up")
            with st.form("manual_followup"):
                candidates = db.query(Candidate).all()
                cand_list = {c.name: c.candidate_id for c in candidates}
                selected_cand = st.selectbox("Select Candidate", options=list(cand_list.keys()))

                # Find candidate's offer
                offer = db.query(Offer).filter(Offer.candidate_id == cand_list[selected_cand]).first()

                followup_date = st.date_input("Scheduled Date")
                channel = st.selectbox("Channel", ["Phone", "Email", "WhatsApp", "LinkedIn"])
                message = st.text_area("Message/Notes")
                f_type = st.selectbox("Type", ["General", "Risk Mitigation", "Closing", "Touch-base"])

                if st.form_submit_button("Schedule Follow-up"):
                    if not message:
                        st.error("Please enter a message.")
                    else:
                        followup_service.FollowupService.schedule_followup(
                            db, cand_list[selected_cand],
                            offer.offer_id if offer else None,
                            followup_date, channel, message, f_type
                        )
                        st.success("Follow-up scheduled successfully!")
                        st.rerun()

    finally:
        db.close()

    st.header("📈 Recruitment Analytics")
    st.caption("Data-driven insights into your hiring pipeline and candidate risk")
    st.divider()

    db = get_db()
    try:
        # 1. High-Level KPIs
        kpis = analytics_service.get_high_level_kpis(db)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Overall Conv. Rate", f"{kpis['conversion_rate']:.1f}%")
        col2.metric("Offer Acceptance", f"{kpis['offer_acceptance_rate']:.1f}%")
        col3.metric("High Risk Candidates", kpis['high_risk_count'])
        col4.metric("Total Pipeline", kpis['total_pipeline'])

        st.divider()

        # 2. Visualizations
        row1_col1, row1_col2 = st.columns([2, 1])

        with row1_col1:
            st.subheader("Pipeline Funnel")
            df_funnel = analytics_service.get_pipeline_stats(db)
            if not df_funnel.empty:
                # Define standard funnel order
                funnel_order = ["Applied", "Screening", "Interview", "Offered", "Joined"]
                df_funnel['Status'] = pd.Categorical(df_funnel['Status'], categories=funnel_order, ordered=True)
                df_funnel = df_funnel.sort_values('Status')

                fig_funnel = px.funnel(df_funnel, x='Count', y='Status',
                                     title="Candidate Flow",
                                     color_discrete_sequence=['#636EFA'])
                st.plotly_chart(fig_funnel, use_container_width=True)
            else:
                st.info("No pipeline data available.")

        with row1_col2:
            st.subheader("Offer Outcomes")
            df_offers = analytics_service.get_offer_conversion_stats(db)
            if not df_offers.empty:
                fig_pie = px.pie(df_offers, values='Count', names='Status',
                               title="Offer Status Distribution",
                               hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No offer data available.")

        st.divider()

        row2_col1, row2_col2 = st.columns(2)

        with row2_col1:
            st.subheader("Risk Distribution")
            df_risk = analytics_service.get_risk_distribution(db)
            if not df_risk.empty:
                fig_risk = px.bar(df_risk, x='Risk Level', y='Count',
                                 title="Candidate Risk Levels",
                                 color='Risk Level',
                                 color_discrete_map={'LOW': 'green', 'MEDIUM': 'orange', 'HIGH': 'red'})
                st.plotly_chart(fig_risk, use_container_width=True)
            else:
                st.info("No risk data available.")

        with row2_col2:
            st.subheader("Source Effectiveness")
            df_source = analytics_service.get_source_effectiveness(db)
            if not df_source.empty:
                fig_source = px.bar(df_source, x='Count', y='Source',
                                   title="Hires by Source",
                                   orientation='h',
                                   color_discrete_sequence=['#AB63FA'])
                st.plotly_chart(fig_source, use_container_width=True)
                # Sort by count for better visibility
                df_source = df_source.sort_values('Count', ascending=False)
            else:
                st.info("No source data available.")

        st.divider()

        st.subheader("Compensation Analysis")
        df_comp = analytics_service.get_compensation_stats(db)
        if not df_comp.empty:
            fig_comp = px.scatter(df_comp, x='Expected CTC', y='Offered CTC',
                                 title="Expected vs Offered Compensation",
                                 labels={'Expected CTC': 'Expected (Annual)', 'Offered CTC': 'Offered (Annual)'},
                                 trendline="ols")
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("No compensation data available.")

    finally:
        db.close()

# --- MAIN NAVIGATION ---
def main():
    # Sidebar
    st.sidebar.title("🚀 RecruiterAI")
    st.sidebar.markdown("---")

    menu_options = {
        "Dashboard": "🏠 Dashboard",
        "Candidates": "👥 Candidates",
        "Jobs": "💼 Jobs",
        "Offers": "📜 Offers",
        "Resume Screening": "🔍 Resume Screening",
        "Risk Monitor": "⚠️ Risk Monitor",
        "Follow-ups": "📅 Follow-ups",
        "Analytics": "📈 Analytics",
        "Settings": "⚙️ Settings"
    }

    for page_name, label in menu_options.items():
        if st.sidebar.button(label, use_container_width=True,
                              on_click=navigate_to, args=(page_name,)):
            pass

    st.sidebar.markdown("---")
    st.sidebar.caption("AI-Powered Risk & Engagement Platform")

    # Page Routing
    if st.session_state.current_page == "Dashboard":
        render_dashboard()
    elif st.session_state.current_page == "Candidates":
        render_candidates()
    elif st.session_state.current_page == "Jobs":
        render_jobs()
    elif st.session_state.current_page == "Offers":
        render_offers()
    elif st.session_state.current_page == "Resume Screening":
        render_resume_screening()
    elif st.session_state.current_page == "Risk Monitor":
        render_risk_monitor()
    elif st.session_state.current_page == "Follow-ups":
        render_followups()
    elif st.session_state.current_page == "Analytics":
        render_analytics()
    elif st.session_state.current_page == "Settings":
        st.info("Settings are coming soon!")

if __name__ == "__main__":
    main()
