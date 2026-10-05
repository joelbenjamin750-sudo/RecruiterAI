import pandas as pd
from sqlalchemy import func
from models import Candidate, Job, Application, Offer, RiskScore

def get_pipeline_stats(db):
    """Returns candidate counts per application status for the funnel chart."""
    results = db.query(Application.status, func.count(Application.application_id))\
                .group_by(Application.status).all()
    return pd.DataFrame(results, columns=['Status', 'Count'])

def get_offer_conversion_stats(db):
    """Returns distribution of offer statuses."""
    results = db.query(Offer.candidate_status, func.count(Offer.offer_id))\
                .group_by(Offer.candidate_status).all()
    return pd.DataFrame(results, columns=['Status', 'Count'])

def get_risk_distribution(db):
    """Returns distribution of risk levels."""
    results = db.query(RiskScore.risk_level, func.count(RiskScore.risk_id))\
                .group_by(RiskScore.risk_level).all()
    return pd.DataFrame(results, columns=['Risk Level', 'Count'])

def get_source_effectiveness(db):
    """Returns total applications grouped by source."""
    results = db.query(Application.source, func.count(Application.application_id))\
                .group_by(Application.source).all()
    return pd.DataFrame(results, columns=['Source', 'Count'])

def get_compensation_stats(db):
    """Returns expected vs offered CTC for scatter plot."""
    results = db.query(Candidate.expected_ctc, Offer.offered_ctc)\
                .join(Offer, Candidate.candidate_id == Offer.candidate_id).all()
    return pd.DataFrame(results, columns=['Expected CTC', 'Offered CTC'])

def get_high_level_kpis(db):
    """Calculates summary metrics for the KPI row."""
    total_apps = db.query(Application).count()
    total_offers = db.query(Offer).count()
    total_joined = db.query(Application).filter(Application.status == 'Joined').count()

    accepted_offers = db.query(Offer).filter(Offer.candidate_status == 'Accepted').count()

    conversion_rate = (total_joined / total_apps * 100) if total_apps > 0 else 0
    offer_acceptance_rate = (accepted_offers / total_offers * 100) if total_offers > 0 else 0

    high_risk_count = db.query(RiskScore).filter(RiskScore.risk_level == 'HIGH').count()

    return {
        "conversion_rate": conversion_rate,
        "offer_acceptance_rate": offer_acceptance_rate,
        "high_risk_count": high_risk_count,
        "total_pipeline": total_apps
    }
