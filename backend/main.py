from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import uuid
from typing import Optional

# Ensure the root of the project is in path so we can import src.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Attempt importing engine modules mapping
try:
    from bam import main as bam_main
except ImportError:
    pass

app = FastAPI(title="AntiGravity BAM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunPipelineRequest(BaseModel):
    client_id: str
    input_file_url: str
    generate_taxonomy: bool = False

class FeedbackRequest(BaseModel):
    run_id: str
    category: str
    rating: int
    comment: Optional[str] = None
    attribute_ref: Optional[str] = None

@app.get("/")
def read_root():
    return {"message": "AntiGravity BAM Backend Engine Online."}

@app.post("/api/run-pipeline")
def run_pipeline(request: RunPipelineRequest, background_tasks: BackgroundTasks):
    run_id = str(uuid.uuid4())
    # TODO: In future, dispatch background task to hit Supabase Storage, run pipeline via src.*, and write results to PSQL
    return {"run_id": run_id, "status": "running"}

@app.get("/api/results/{run_id}")
def get_results(run_id: str):
    # Mock response
    return {
        "status": "completed",
        "summary": {
            "total_messages": 10000,
            "total_bigrams": 4523,
            "tagged_pct": 78.5,
            "positive_pct": 56.2
        },
        "output_file_url": f"https://supabase.dummy/storage/outputs/{run_id}.xlsx"
    }

@app.post("/api/feedback")
def submit_feedback(req: FeedbackRequest):
    return {"status": "success", "feedback_recorded": True}
