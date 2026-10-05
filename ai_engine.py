import os
from analyzer import run_local_analysis

def analyze_candidate(jd, resume):
    """
    Interface for app.py. Calls the actual analysis logic in analyzer.py.
    """
    try:
        return run_local_analysis(jd, resume)
    except Exception as e:
        return f"**Analysis Error:** A technical error occurred during the local analysis.\n\nDetails: {e}"
