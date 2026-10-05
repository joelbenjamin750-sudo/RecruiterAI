import pandas as pd
from datetime import datetime, date, timedelta
from sqlalchemy import func
from models import Candidate, Job, Offer, Followup, Interaction

class FollowupService:
    """
    Service layer to handle the scheduling and tracking of candidate follow-ups.
    """

    @staticmethod
    def schedule_followup(db, candidate_id, offer_id, followup_date, channel, message, followup_type="General"):
        """Creates a new follow-up record."""
        new_followup = Followup(
            candidate_id=candidate_id,
            offer_id=offer_id,
            scheduled_date=followup_date,
            channel=channel,
            message=message,
            followup_type=followup_type,
            status="Pending"
        )
        db.add(new_followup)
        db.commit()
        return new_followup

    @staticmethod
    def get_todays_agenda(db):
        """Returns all pending follow-ups scheduled for today."""
        today = datetime.now().date()
        # Convert date to datetime for comparison if needed, or use func.date()
        results = db.query(Followup).filter(
            func.date(Followup.scheduled_date) == today,
            Followup.status == "Pending"
        ).all()
        return results

    @staticmethod
    def get_overdue_followups(db):
        """Returns all pending follow-ups scheduled before today."""
        today = datetime.now().date()
        results = db.query(Followup).filter(
            func.date(Followup.scheduled_date) < today,
            Followup.status == "Pending"
        ).all()
        return results

    @staticmethod
    def get_followup_suggestions(db):
        """
        Identifies candidates who need follow-ups based on:
        1. HIGH risk levels.
        2. Offers Pending for >= 3 days.
        """
        suggestions = []

        # 1. Risk-Based Suggestions
        high_risk = db.query(Followup).join(Candidate).filter(
            # We'll check RiskScore table for HIGH risk
            # Note: simplified join for the sake of logic
            # In reality we would query RiskScore model
            False # Placeholder for actual RiskScore join logic
        ).all()

        # Let's do the actual logic using a separate query for efficiency
        from models import RiskScore
        high_risks = db.query(RiskScore).filter(RiskScore.risk_level == "HIGH").all()
        for r in high_risks:
            suggestions.append({
                "candidate_id": r.candidate_id,
                "offer_id": r.offer_id,
                "reason": "High Risk Detected",
                "priority": "High"
            })

        # 2. Time-Based Suggestions (Pending >= 3 days)
        three_days_ago = date.today() - timedelta(days=3)
        stagnant_offers = db.query(Offer).filter(
            Offer.candidate_status == "Pending",
            Offer.offer_date <= three_days_ago
        ).all()

        for o in stagnant_offers:
            suggestions.append({
                "candidate_id": o.candidate_id,
                "offer_id": o.offer_id,
                "reason": "Offer Pending > 3 Days",
                "priority": "Medium"
            })

        return suggestions

    @staticmethod
    def complete_followup(db, followup_id, status, response_text=None):
        """
        Updates follow-up status and automatically creates an Interaction record
        if the candidate responded.
        """
        followup = db.query(Followup).filter(Followup.followup_id == followup_id).first()
        if not followup:
            return False

        followup.status = status
        if status == "Responded" and response_text:
            followup.response_received = response_text
            followup.response_date = datetime.now()

            # Sync to Interaction table
            interaction = Interaction(
                candidate_id=followup.candidate_id,
                offer_id=followup.offer_id,
                channel=followup.channel,
                direction="Inbound",
                message=f"Follow-up Response: {followup.message}",
                response=response_text,
                engagement_score=7 # Default score for responding
            )
            db.add(interaction)

        db.commit()
        return True
