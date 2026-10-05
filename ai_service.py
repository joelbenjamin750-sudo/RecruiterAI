import os
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class AIService:
    def __init__(self):
        # Open-source APIs usually require a Base URL (e.g., http://localhost:11434/v1 for Ollama)
        # and an API key (which might be a dummy string for local models).
        self.api_key = os.getenv("AI_API_KEY", "dummy-key")
        self.base_url = os.getenv("AI_BASE_URL", "http://localhost:11434/v1")
        self.model_name = os.getenv("AI_MODEL_NAME", "llama3") # Default to llama3, change as needed

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    async def analyze_candidate_fit(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """
        Analyzes a candidate's resume against a job description using an open-source LLM.
        """
        # The prompt remains the same as it's model-agnostic logic
        prompt = f"""
        You are an expert Technical Recruiter. Your task is to analyze a candidate's resume against a specific job description.

        JOB DESCRIPTION:
        {job_description}

        CANDIDATE RESUME:
        {resume_text}

        Please provide a highly objective analysis. Return your response EXACTLY in the following format:
        SCORE: [A number from 0 to 100]
        SUMMARY: [A one-sentence high-level summary of the fit]
        REASONING: [A detailed explanation of why the candidate fits or doesn't fit, focusing on skills, experience, and gaps]
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a professional recruitment AI that only outputs data in the requested format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )

            response_text = response.choices[0].message.content
            return self._parse_ai_response(response_text)

        except Exception as e:
            print(f"Error during AI analysis: {e}")
            return {
                "error": str(e),
                "score": 0,
                "summary": "Analysis failed.",
                "fit_reasoning": "An error occurred while calling the AI service."
            }

    def _parse_ai_response(self, text: str) -> Dict[str, Any]:
        """
        Helper to parse the structured text response from the LLM into a dictionary.
        """
        result = {"score": 0, "summary": "", "fit_reasoning": ""}

        lines = text.split('\n')
        for line in lines:
            if "SCORE:" in line:
                try:
                    # Extract number from "SCORE: 85"
                    numeric_part = ''.join(filter(str.isdigit, line))
                    result["score"] = int(numeric_part) if numeric_part else 0
                except ValueError:
                    result["score"] = 0
            elif "SUMMARY:" in line:
                result["summary"] = line.split("SUMMARY:", 1)[1].strip()
            elif "REASONING:" in line:
                result["fit_reasoning"] = line.split("REASONING:", 1)[1].strip()

        return result
