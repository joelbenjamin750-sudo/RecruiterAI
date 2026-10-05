from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from database import Base

class Candidate(Base):
    __tablename__ = "candidates"

    candidate_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    current_company = Column(String)
    current_designation = Column(String)
    total_experience = Column(Float)
    skills = Column(Text)
    current_ctc = Column(Float)
    expected_ctc = Column(Float)
    notice_period = Column(Integer) # Days
    location = Column(String)
    preferred_location = Column(String)
    work_mode = Column(String) # Remote, Hybrid, Onsite
    reason_for_change = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(Integer, primary_key=True, index=True)
    client = Column(String, nullable=False)
    job_title = Column(String, nullable=False)
    technology = Column(String)
    location = Column(String)
    work_mode = Column(String)
    experience_min = Column(Float)
    experience_max = Column(Float)
    salary_min = Column(Float)
    salary_max = Column(Float)
    notice_requirement = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Application(Base):
    __tablename__ = "applications"

    application_id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.candidate_id"))
    job_id = Column(Integer, ForeignKey("jobs.job_id"))
    source = Column(String)
    status = Column(String) # Applied, Screening, Interview, Offered, Rejected, Joined
    applied_date = Column(Date)
    interview_status = Column(String)

class Offer(Base):
    __tablename__ = "offers"

    offer_id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.candidate_id"))
    job_id = Column(Integer, ForeignKey("jobs.job_id"))
    offer_date = Column(Date)
    joining_date = Column(Date)
    offered_ctc = Column(Float)
    fixed_ctc = Column(Float)
    variable_ctc = Column(Float)
    candidate_status = Column(String) # Pending, Accepted, Declined, Withdrawn
    accepted_date = Column(Date)
    withdrawn_date = Column(Date)
    joined_date = Column(Date)
    counteroffer = Column(String) # Yes/No
    competing_offer = Column(String) # Yes/No
    competing_offer_ctc = Column(Float)
    dropout_reason = Column(String)
    dropout_notes = Column(Text)

class Interaction(Base):
    __tablename__ = "interactions"

    interaction_id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.candidate_id"))
    offer_id = Column(Integer, ForeignKey("offers.offer_id"), nullable=True)
    interaction_date = Column(DateTime(timezone=True), server_default=func.now())
    channel = Column(String) # Email, Phone, WhatsApp, LinkedIn
    direction = Column(String) # Inbound, Outbound
    message = Column(Text)
    response = Column(Text)
    sentiment = Column(String)
    engagement_score = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RiskScore(Base):
    __tablename__ = "risk_scores"

    risk_id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.candidate_id"))
    offer_id = Column(Integer, ForeignKey("offers.offer_id"))
    risk_score = Column(Integer)
    risk_level = Column(String) # LOW, MEDIUM, HIGH
    counteroffer_risk = Column(Integer)
    competing_offer_risk = Column(Integer)
    notice_period_risk = Column(Integer)
    compensation_risk = Column(Integer)
    location_risk = Column(Integer)
    engagement_risk = Column(Integer)
    key_risks = Column(Text)
    recommended_action = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Followup(Base):
    __tablename__ = "followups"

    followup_id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.candidate_id"))
    offer_id = Column(Integer, ForeignKey("offers.offer_id"))
    followup_type = Column(String)
    scheduled_date = Column(DateTime(timezone=True))
    channel = Column(String)
    message = Column(Text)
    status = Column(String) # Pending, Sent, Responded
    response_received = Column(String)
    response_date = Column(DateTime(timezone=True))
