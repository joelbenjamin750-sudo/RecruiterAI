import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import urllib.parse
import streamlit as st

# Load environment variables from .env file for local development
load_dotenv()

def get_database_url():
    \"\"\"
    Retrieves the database connection string.
    Prioritizes Streamlit secrets (for cloud) then falls back to .env (for local).
    \"\"\"
    # 1. Try Streamlit Secrets (Cloud)
    if \"DB_URL\" in st.secrets:
        return st.secrets[\"DB_URL\"]

    # 2. Try .env / Environment Variables (Local)
    db_user = os.getenv(\"DB_USER\", \"postgres\")
    db_pass = os.getenv(\"DB_PASSWORD\", \"password\")
    db_host = os.getenv(\"DB_HOST\", \"localhost\")
    db_port = os.getenv(\"DB_PORT\", \"5432\")
    db_name = os.getenv(\"DB_NAME\", \"recruiter_ai\")

    # URL-encode the password to handle special characters
    encoded_pass = urllib.parse.quote_plus(db_pass)
    return f\"postgresql://{db_user}:{encoded_pass}@{db_host}:{db_port}/{db_name}\"

# SQLAlchemy Connection String
DATABASE_URL = get_database_url()

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a base class for our models to inherit from
Base = declarative_base()

# Create a configured \"Session\" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    \"\"\"
    Helper function to get a database session.
    \"\"\"
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    \"\"\"
    Creates all tables defined in models.py
    \"\"\"
    import models # Import models to ensure they are registered with Base
    Base.metadata.create_all(bind=engine)
