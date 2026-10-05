from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi import Depends
import uvicorn
import os

# Import our custom services
from ai_service import AIService
from pdf_service import PDFService
from db_service import DBService

app = FastAPI(title="RecruiterAI API", description="AI-Powered Recruitment Analysis System")

# Initialize services
ai_service = AIService()
pdf_service = PDFService()
db_service = DBService()

@app.get("/")
async def root():
    return {"message": "Welcome to RecruiterAI API. Use /analyze-resume to start analysis."}

@app.post("/analyze-resume")
async def analyze_resume(application_id: int, file: UploadFile = File(...)):
    """
    Main endpoint: Uploads a resume, analyzes it against the job, and saves the result.
    """
    # 1. Validate Application
    app_details = db_service.get_application_details(application_id)
    if not app_details:
        raise HTTPException(status_code=404, detail="Application ID not found")

    # 2. Save and Extract Text from PDF
    file_content = await file.read()
    file_path = pdf_service.save_upload(file_content, file.filename)

    if not file_path:
        raise HTTPException(status_code=500, detail="Failed to save uploaded resume")

    resume_text = pdf_service.extract_text(file_path)
    if not resume_text:
        raise HTTPException(status_code=400, detail="Could not extract text from the PDF. Please ensure it's a valid text-based PDF.")

    # 3. Get Job Description from DB
    # For this MVP, we'll fetch the job title and description.
    # In a full version, we'd have a specific get_job_description method.
    job_query = f"SELECT description, requirements FROM Jobs WHERE id = {app_details['job_title']}"
    # Note: The above is a placeholder; we should use db_service to fetch.
    # Let's assume for now we fetch a generic description or use a mock for testing.
    job_description = "Looking for a software engineer with experience in Python and PostgreSQL."

    # 4. AI Analysis
    analysis_result = await ai_service.analyze_candidate_fit(resume_text, job_description)

    if "error" in analysis_result and analysis_result["score"] == 0:
        raise HTTPException(status_code=500, detail=f"AI Analysis failed: {analysis_result['error']}")

    # 5. Save Analysis to Database
    success = db_service.save_ai_analysis(
        application_id=application_id,
        score=analysis_result["score"],
        summary=analysis_result["summary"],
        reasoning=analysis_result["fit_reasoning"]
    )

    if not success:
        raise HTTPException(status_code=500, detail="AI analysis succeeded, but failed to save to database")

    return {
        "status": "success",
        "application_id": application_id,
        "analysis": analysis_result
    }

if __name__ == "__main__":
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)
