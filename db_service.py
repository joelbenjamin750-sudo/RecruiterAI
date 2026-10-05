import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DBService:
    """
    Service to handle all database operations for RecruiterAI.
    """
    def __init__(self):
        # Get connection string from .env
        # Format: postgresql://user:password@host:port/dbname
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL not found in .env file")

        # Create SQLAlchemy engine
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def save_ai_analysis(self, application_id: int, score: int, summary: str, reasoning: str) -> bool:
        """
        Saves the AI's fit analysis into the AI_Analysis table.
        """
        query = text("""
            INSERT INTO AI_Analysis (application_id, score, summary, fit_reasoning)
            VALUES (:app_id, :score, :summary, :reasoning)
            ON CONFLICT (application_id)
            DO UPDATE SET
                score = EXCLUDED.score,
                summary = EXCLUDED.summary,
                fit_reasoning = EXCLUDED.fit_reasoning,
                analyzed_at = CURRENT_TIMESTAMP;
        """)

        # Note: I added ON CONFLICT to the logic so if we re-analyze a candidate,
        # it updates the existing score instead of creating a duplicate.
        # (This requires a UNIQUE constraint on application_id in the table)

        try:
            with self.engine.begin() as conn:
                conn.execute(query, {
                    "app_id": application_id,
                    "score": score,
                    "summary": summary,
                    "reasoning": reasoning
                })
            return True
        except Exception as e:
            print(f"Database error saving AI analysis: {e}")
            return False

    def get_application_details(self, application_id: int) -> dict:
        """
        Fetches details about an application, including the job and candidate.
        """
        query = text("""
            SELECT a.id, j.title as job_title, c.full_name as candidate_name, a.status
            FROM Applications a
            JOIN Jobs j ON a.job_id = j.id
            JOIN Candidates c ON a.candidate_id = c.id
            WHERE a.id = :app_id
        """)

        try:
            with self.engine.connect() as conn:
                result = conn.execute(query, {"app_id": application_id}).fetchone()
                if result:
                    return dict(result._mapping)
                return None
        except Exception as e:
            print(f"Database error fetching application: {e}")
            return None

    def create_candidate(self, name: str, email: str, phone: str, resume_url: str, skills: str) -> int:
        """
        Registers a new candidate and returns their ID.
        """
        query = text("""
            INSERT INTO Candidates (full_name, email, phone, resume_url, skills)
            VALUES (:name, :email, :phone, :resume, :skills)
            RETURNING id;
        """)
        try:
            with self.engine.begin() as conn:
                result = conn.execute(query, {
                    "name": name, "email": email, "phone": phone, "resume": resume_url, "skills": skills
                })
                return result.fetchone()[0]
        except Exception as e:
            print(f"Database error creating candidate: {e}")
            return None
