import pandas as pd
from sqlalchemy import func
from models import Candidate, Job, Offer, RiskScore, Interaction

class RiskCalculationEngine:
    """
    Engine to calculate recruitment risk scores based on candidate and offer data.
    Scores are normalized to 0-100.
    """

    WEIGHTS = {
        "counteroffer": 0.30,
        "competing_offer": 0.20,
        "notice_period": 0.20,
        "compensation": 0.15,
        "location": 0.10,
        "engagement": 0.05
    }

    @staticmethod
    def calculate_risk(db, candidate_id, offer_id):
        # Fetch necessary data
        candidate = db.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
        offer = db.query(Offer).filter(Offer.offer_id == offer_id).first()
        job = db.query(Job).filter(Job.job_id == offer.job_id).first()

        if not candidate or not offer or not job:
            return None

        scores = {}

        # 1. Counter-offer Risk (0 or 10)
        scores["counteroffer"] = 10 if offer.counteroffer == 'Yes' else 0

        # 2. Competing Offer Risk (0 or 10)
        scores["competing_offer"] = 10 if offer.competing_offer == 'Yes' else 0

        # 3. Notice Period Risk (0, 5, 10)
        # Logic: Compare candidate notice period with job requirement
        # Note: Job.notice_requirement is a string, we'll try to extract numbers or use defaults
        cand_notice = candidate.notice_period or 0
        # Simple heuristic for notice requirement: assume 30 days if not specified
        req_notice = 30
        if cand_notice > req_notice + 30:
            scores["notice_period"] = 10
        elif cand_notice > req_notice:
            scores["notice_period"] = 5
        else:
            scores["notice_period"] = 0

        # 4. Compensation Risk (0, 5, 10)
        # Gap between expected and offered
        expected = candidate.expected_ctc or 1
        offered = offer.offered_ctc or 0
        gap = (expected - offered) / expected
        if gap > 0.10:
            scores["compensation"] = 10
        elif gap > 0.05:
            scores["compensation"] = 5
        else:
            scores["compensation"] = 0

        # 5. Location Risk (0, 5, 10)
        # Simple match check
        if candidate.location == job.location:
            scores["location"] = 0
        elif candidate.preferred_location == job.location or candidate.work_mode == "Remote":
            scores["location"] = 5
        else:
            scores["location"] = 10

        # 6. Engagement Risk (0, 5, 10)
        # Average of last 3 interaction engagement scores
        interactions = db.query(Interaction).filter(Interaction.candidate_id == candidate_id)\
                        .order_by(Interaction.interaction_date.desc()).limit(3).all()
        if interactions:
            avg_engagement = sum(i.engagement_score for i in interactions if i.engagement_score) / len(interactions)
            if avg_engagement < 5:
                scores["engagement"] = 10
            elif avg_engagement < 8:
                scores["engagement"] = 5
            else:
                scores["engagement"] = 0
        else:
            scores["engagement"] = 5 # Neutral if no data

        # Final weighted score calculation (Total is out of 10)
        total_score_out_of_10 = sum(scores[k] * self.WEIGHTS[k] for k in self.WEIGHTS)
        final_score = int(total_score_out_of_10 * 10) # Scale to 0-100

        # Map to Risk Level
        if final_score < 30:
            level = "LOW"
        elif final_score <= 60:
            level = "MEDIUM"
        else:
            level = "HIGH"

        # Generate recommended action
        action = "Continue standard engagement."
        if level == "HIGH":
            action = "Immediate intervention required. Review compensation and competing offers."
        elif level == "MEDIUM":
            action = "Increase touchpoints and verify commitment."

        # Store in database
        risk_record = db.query(RiskScore).filter(
            RiskScore.candidate_id == candidate_id,
            RiskScore.offer_id == offer_id
        ).first()

        if not risk_record:
            risk_record = RiskScore(candidate_id=candidate_id, offer_id=offer_id)
            db.add(risk_record)

        risk_record.risk_score = final_score
        risk_record.risk_level = level
        risk_record.counteroffer_risk = scores["counteroffer"]
        risk_record.competing_offer_risk = scores["competing_offer"]
        risk_record.notice_period_risk = scores["notice_period"]
        risk_record.compensation_risk = scores["compensation"]
        risk_record.location_risk = scores["location"]
        risk_record.engagement_risk = scores["engagement"]
        risk_record.recommended_action = action

        db.commit()
        return risk_record

def get_high_risk_candidates(db):
    """Returns candidates with HIGH risk level."""
    return db.query(RiskScore).filter(RiskScore.risk_level == "HIGH").all()

def update_risk_manually(db, risk_id, new_level, new_action):
    """Allows recruiters to manually override risk metrics."""
    risk = db.query(RiskScore).filter(RiskScore.risk_id == risk_id).first()
    if risk:
        risk.risk_level = new_level
        risk.recommended_action = new_action
        db.commit()
        return True
    return False
