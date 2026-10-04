import os
import tempfile
import json
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import Response

# Import the root SequentialAgent pipeline
# from resume_fit_agent.agent import root_agent

app = FastAPI(title="Resume Fit API", description="ADK-based Resume Optimizer Pipeline")

@app.post("/api/v1/resume/optimize")
async def optimize_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    # Verify file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(status_code=400, detail="Only .pdf, .docx, and .txt files are supported")
    
    file_bytes = await file.read()
    
    # We will pass file_bytes and filename into the pipeline state
    # Wait, adk requires sequential agent. We will invoke it.
    
    return {"message": "Endpoint created"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
