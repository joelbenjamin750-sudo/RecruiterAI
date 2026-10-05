import re
from collections import Counter

class ResumeAnalyzer:
    """Analyzes extracted resume text against job requirements using advanced keyword and pattern matching."""

    def analyze(self, resume_text, job_description):
        """
        Performs a detailed analysis to determine match percentage and extract key info.
        """
        # 1. Extract sets of keywords
        jd_keywords = self._extract_keywords(job_description)
        resume_keywords = self._extract_keywords(resume_text)

        if not jd_keywords:
            return {"score": 0, "matched": [], "missing": [], "summary": "No requirements found in JD."}

        matched = jd_keywords.intersection(resume_keywords)
        missing = jd_keywords.difference(resume_keywords)

        # Calculate score based on keyword intersection
        score = (len(matched) / len(jd_keywords)) * 100

        # 2. Heuristic-based Experience Extraction
        exp_info = self._extract_experience(resume_text)

        return {
            "score": round(score, 2),
            "matched": list(matched),
            "missing": list(missing),
            "experience": exp_info,
            "summary": f"Candidate matches {len(matched)} out of {len(jd_keywords)} key requirements."
        }

    def _extract_keywords(self, text):
        """Extracts meaningful technical keywords, ignoring common stop words."""
        stop_words = {
            'and', 'the', 'with', 'for', 'from', 'that', 'this', 'your', 'their',
            'about', 'which', 'would', 'could', 'should', 'experience', 'skills',
            'knowledge', 'required', 'preferred', 'candidate', 'resume', 'professional'
        }
        words = re.findall(r'\b\w{3,}\b', text.lower())
        return set([w for w in words if w not in stop_words])

    def _extract_experience(self, text):
        """Attempts to find experience markers (e.g., '5 years', '3+ yrs')."""
        patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?experience',
            r'experience\s*(?:of)?\s*(\d+)\+?\s*(?:years?|yrs?)'
        ]
        found_years = []
        for p in patterns:
            matches = re.findall(p, text, re.IGNORECASE)
            found_years.extend([int(m) for m in matches])

        return max(found_years) if found_years else "Not specified"

def run_local_analysis(jd_text, cv_text):
    """
    Actual logic to perform the analysis.
    Renamed from analyze_candidate to avoid collision with ai_engine.py.
    """
    analyzer = ResumeAnalyzer()
    analysis = analyzer.analyze(cv_text, jd_text)

    score = analysis["score"]
    matched = ", ".join(analysis["matched"]) if analysis["matched"] else "None"
    missing = ", ".join(analysis["missing"]) if analysis["missing"] else "None"
    exp = analysis["experience"]

    if score >= 75:
        rec = "SHORTLIST"
    elif score >= 40:
        rec = "REVIEW"
    else:
        rec = "NOT SUITABLE"

    return f"""
### 📊 Candidate Analysis Result (Local Engine)

**OVERALL FITMENT: {score}%**

**TOTAL EXPERIENCE:**
- {exp} years (approx)

**RELEVANT EXPERIENCE:**
- Based on keyword match: {score}% alignment with JD requirements.

**SKILL MATCH:**
- **Matched Skills:** {matched}
- **Missing Skills:** {missing}

**JD vs CV COMPARISON:**
The candidate's profile shows a {score}% overlap with the required technical stack.
Key strengths are identified in the matched skills listed above.

**RECRUITER SUMMARY:**
{analysis['summary']} The candidate demonstrates a { 'strong' if score > 70 else 'moderate' if score > 40 else 'low' } match for this specific role based on available text data.

**FINAL RECOMMENDATION:**
**{rec}**
"""
